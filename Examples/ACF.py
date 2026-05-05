
import numpy as np
import csv

#Finds the Autocorrelation for a given lag 
def ACF(buffer, lag):
    R = 0 
    if lag == 0:
        R = np.sum(buffer * buffer) 
    else:
        R = np.sum(buffer[:-lag] * buffer[lag:])
    return R

#find the local maxima by looking to the right and left of a sample, makes a list of all observed maxima and returns it
def findLocalMaxima(corrs):
    size = len(corrs)
    maxima = []
    for lag in range(1, size - 1):
        if (corrs[lag] >= corrs[lag - 1] and corrs[lag] >= corrs[lag + 1]): 
            maxima.append(lag)
    #print(maxima)
    return maxima

def findLocalMaximaInter(corrs):
    corrs = np.array(corrs)
    maxima = np.array(findLocalMaxima(corrs))
    if len(maxima) == 0:
        return maxima
    return maxima + 0.5 * (corrs[maxima - 1] - corrs[maxima + 1]) / \
                         (corrs[maxima - 1] - 2 * corrs[maxima] + corrs[maxima + 1])

def getFreq(corrs, fs, interpolate=True):
    maxima = findLocalMaximaInter(corrs)
    if len(maxima) < 2:
        return 0
    # Average period over all found maxima
    return fs * (len(maxima) - 1) / (maxima[-1] - maxima[0])

#find the correlation values for the entire buffer, return a list of corrs corresponding to different lag values
def getCorr(samps, method='fft'):
    if method == 'fft':
        n = len(samps)
        fft = np.fft.rfft(samps, n=2 * n)
        power = fft * np.conj(fft)
        corrs = np.fft.irfft(power)[:n]
        return corrs.real
    
    elif method == 'direct':
        corrs = []
        for lag in range(0, len(samps)):
            corrs.append(ACF(samps, lag))
        return corrs
    
    else:
        raise ValueError(f"Unknown method '{method}'. Choose 'fft' or 'direct'.")

#scales the data between -1 and 1
def maxAbsoluteScaling(data):
    data = [abs(element) for element in data]
    xMax = max(data)
    data = [element / xMax for element in data]
    return data

#Generates a buffer of pure Sin wave given a frequency and sampling frequency and a number of samples
def genSin(f, fs, numSamp):
    n = np.arange(0, numSamp)
    samps = np.sin(2 * np.pi * (f / fs) * n)
    return samps

#gets the error in cents between two given frequencies
def getCentsError(fn, freqCalc):
    if freqCalc <= 0:
        return "div/0 error"
    return 1200 * np.log2(freqCalc / fn)

def quadInterpolate(x, x0, y0, x1, y1, x2, y2):
    L0 = (x - x1) * (x - x2) / ((x0 - x1) * (x0 - x2))
    L1 = (x - x0) * (x - x2) / ((x1 - x0) * (x1 - x2))
    L2 = (x - x0) * (x - x1) / ((x2 - x0) * (x2 - x1))
    return y0 * L0 + y1 * L1 + y2 * L2

#Creates a loop that increases the sampling frequency and lists key values into csv 
with open('ACFTest48khz.csv', 'w', newline = '') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Write the header row
    csvwriter.writerow(['Sampling Frequency', 'True Frequency', 'Frequency Calculated', 'Cents Error', 'ACF Vals:'])

    #fn = 800 #about the freq of low e string guitar fundamental
    fs = 48000
    fn = 970
    numcycles = 10
    for fn in range(50, 1000, 50):
        numSamps = round(fs / fn * 10) #generates 3 cycles of signal
        samps = genSin(fn, fs, numSamps)
        corrs = getCorr(samps) #get ACF values for various lag 
        freqCalc = getFreq(corrs, fs)
        roundedcorrs = [round(corr, 3) for corr in corrs]
        centserror = getCentsError(fn, freqCalc)
        csvwriter.writerow([fs, fn, freqCalc, centserror])
    print("Done")






