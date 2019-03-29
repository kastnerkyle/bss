import numpy as np
from numpy.linalg import inv
from scipy.signal import stft, istft


# suppose that the number of sources and microphones are equal.

# M : # of channels whose index is m
# K : # of frequency bins whose index is k
# T : # of time frames whose index is t

class IVA:

    def __init__(self, x, sample_freq, win='hanning', nperseg=256, noverlap=128):
        '''
        @param(win):str, desired window to use.
        @param(nperseg): length of each segment.
        @param(noverlap): number of points to overlap between segments.
        '''
        self.max_iter = 30
        self.eta = 1.0 * 10 ** (-4)  # is step size
        self.m_shit = 5
        self.x = np.array(x)
        self.sample_freq = sample_freq
        self.win = win
        self.nperseg = nperseg
        self.noverlap = noverlap

    def iva(self):
        '''
        X is complex64-type-3-dementional array whose x axis is microphie , y axis is the segment times, z is frequency respectively.
        @output(x_prd): 2 dimensional array whose 1st axis is the source index, 2nd is data of them.
        '''

        f, _, X = stft(self.x, self.sample_freq, self.win, self.nperseg, self.noverlap)
        # X is (channel index, freq index, time segment idex)

        y = self.reconstruct(X)

        _, x_prd = istft(y, self.sample_freq, self.win, self.nperseg, self.noverlap)

        return x_prd

    def reconstruct(self, X):
        '''
        This func is the way of permutation.
        @param(f): frequency array.
        @param(X): stft of time series x.
        @output(y):y is 3 dementional array
                   whose 1st axis is source index 2nd axis is frequency index and 3rd is time segment index.
        '''

        w = self.__optimize(X)
        y = np.empty(X.shape, dtype=np.complex64)
        for k in range(X.shape[1]):
            y[:,k,:] = np.dot(w[k,:,:], X[:,k,:])

        return y

    def __fai_func(self, y):
        # y is (channel index, freq index)
        # return is (channel index, freq index)
        return np.array(y / np.matrix(np.sqrt(np.sum(np.abs(y)**2, axis=1))).T)

    def __alpha(self, y):
        # y is (channel index, freq index, time segment index)
        M, K, T = y.shape
        alpha = np.zeros((K, M, M), dtype=np.complex64)
        for t in range(T):
            fai = self.__fai_func(y[:,:,t])
            for k in range(K):
                alpha[k,:,:] += np.dot(np.matrix(fai[:,k]).T, np.matrix(y[:,k,t].conjugate()))
        alpha = alpha / T
        return np.array(alpha)

    def __adjust(self, w):
        w = np.dot(np.diag(np.diag(inv(w))), w)
        return w

    def __optimize(self, X):
        M, K, T = X.shape
        w = np.zeros((K, M, M), dtype=np.complex64)
        y = np.empty((M, K, T), dtype=np.complex64)
        for k in range(K):
            w[k,:,:] += np.eye(M)

        for i in range(self.max_iter):
            for k in range(K):
                y[:,k,:] = np.dot(w[k,:,:], X[:,k,:])
            alpha = self.__alpha(y)
            for k in range(K):
                w[k,:,:] += self.eta * np.dot((np.eye(M) - alpha[k,:,:]), w[k,:,:])
            print("{}/{}\n".format(i, self.max_iter))

        for k in range(K):
            w[k,:,:] = self.__adjust(w[k,:,:])

        return w