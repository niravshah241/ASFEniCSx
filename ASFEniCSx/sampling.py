import numpy as np
import json

from ASFEniCSx.utils import NumpyEncoder

class sampling:
    """Class for sampling the domain of a parameter space

    This class produces an object containing the samples of the domain as well
    as the number of samples and the dimension of the parameter space.

    Per default the domain is sampled using a uniform distribution with values
    between -1 and 1.

    Important remarks: No mather what probability density function is used to 
    generate the samples, the samples must always be normalized to the interval
    [-1,1] in order to be used in the active subspace method.

    The samples are stored in a numpy array of shape (M,m) where M is the number
    of samples and m is the dimension of the parameter space.

    The class also provides a method to extract a single sample from the array and
    a method to get the whole sampling array.

    Attributes:
    public:
        M (int): Number of samples
        m (int): Dimension of the parameter space
    private:
        _array (numpy.ndarray): Array containing the samples
    
    Methods:
    public:
        random_uniform(overwrite : bool) -> None: Generates the samples using a uniform distribution  
        extract(index : int) -> numpy.ndarray: Extracts a single sample from the array
        replace(index : int, sample : numpy.ndarray) -> None: Replaces a single sample in the array
        samples() -> numpy.ndarray: Returns the sampling array
        assign_values(f : callable) -> None: Assigns values to the samples using a function
        assign_value(index : int, value : float) -> None: Assigns a value to a single sample
        add_sample(sample : numpy.ndarray) -> None: Adds a sample to the sampling array or adds newly generated sample
        extract_value(index : int) -> numpy.ndarray: Extracts the value of the sample at the given index
        values() -> numpy.ndarray: Returns the array containing the values of the samples
        index(sample : numpy.ndarray) -> int: Returns the index of the given sample in the sampling array
        save(filename : str) -> None: Saves the sampling object to a json file
        load(data : numpy.ndarray, overwrite : boolean) -> None: Loads the sampling object from a numpy array

    Example:
        >>> samples = sampling(100, 10)

    Version:
        0.1
    Contributors:
        Niklas Hornischer (nh605@cam.ac.uk)
    """
    def __init__(self, M : int, m : int, debug=True):
        """Constructor for the sampling object

        Sets the sampling attributes M and m to the values passed to the
        constructor and calls the random_uniform method to generate the samples.

        Args:
            M (int): Number of samples
            m (int): Dimension of the parameter space
            debug (bool, optional): If True, prints debug information. Default is False.

        Raises: 
            AssertionError: If M or m are not greater than 0
        """
        assert M > 0, "Number of samples must be greater than 0"
        assert m > 0, "Dimension of parameter space must be greater than 0"

        self.object_type = "sampling"
        self.M = M
        self.m = m
        self.random_uniform()
        self._debug = debug

    def random_uniform(self, overwrite = False):
        """Generates the samples using a uniform distribution
        
        Generates the samples using a uniform distribution with values between -1 and 1.
        
        Args:
            overwrite (bool, optional): If True, overwrites the existing samples. Default is False.
            
        Raises:
            AttributeError: If the samples already exist and overwrite is False
            
        """
        if not hasattr(self, "_array") or overwrite:
            self._array = np.random.uniform(-1, 1, (self.M,self.m))
        else:
            raise AttributeError("Samples already exist. Use overwrite=True to overwrite them")
    
    def extract(self, index : int):
        """Extracts a single sample from the array
        
        Args:   
            index (int): Index of the sample to be extracted
        
        Returns:
            numpy.ndarray: The sample at the given index

        Raises:
            AssertionError: If the index is out of bounds
        """
        assert 0<= index < self.M, "Index out of bounds"
        return self._array[index,:]
    
    def replace(self, index : int, sample : np.ndarray):
        """Replaces a single sample in the array
        
        Args:
            index (int): Index of the sample to be replaced
            sample (numpy.ndarray): The new sample
        
        Raises:
            AssertionError: If the index is out of bounds
        """
        assert 0<= index < self.M, "Index out of bounds"
        assert sample.shape == (self.m,), "Sample has wrong shape"
        self._array[index,:] = sample

    def add_sample(self, sample : np.ndarray or None):
        """Adds a sample to the sampling array

        Args:
            sample (numpy.ndarray or None): The sample to be added

        Raises:
            AssertionError: If the sample has the wrong shape
        """
        if sample is None:
            sample = np.random.uniform(-1, 1, self.m)
        else:
            assert sample.shape == (self.m,), "Sample has wrong shape"
        self._array = np.vstack((self._array, sample))
        self.M += 1
        pass
    
    def samples(self):
        """Returns the sampling array
        
        Returns:
            numpy.ndarray: The sampling array
        """
        return self._array

    def assign_values(self, f : callable):
        """Assigns values to the sampling object

        Assigns values to the sampling object by evaluating the given function at the samples.

        Args:
            f (callable): The function to be evaluated

        Raises:
            TypeError: If the function is not callable
        """
        assert callable(f), "Function must be callable"
        self._values = np.apply_along_axis(f, 1, self._array)

    def assign_value(self, index : int, value : float):
        """Assigns a value to the sample at given index
        
        Args:
            index (int): Index of the sample
            value (float): The value to be assigned to the sample
        
        Raises:
            AssertionError: If the index is out of bounds
        """
        assert 0<= index < self.M, "Index out of bounds"
        if not hasattr(self, "_values"):
            self._values = np.zeros(self.M)
        self._values[index] = value

    def extract_value(self, index : int):
        """Returns the value assigned to the sample at given index
        
        Args:
            index (int): Index of the sample
        
        Returns:
            float: The value assigned to the sample at the given index

        Raises:
            AssertionError: If the index is out of bounds
            AttributeError: If the values have not been assigned yet
        """
        assert 0<= index < self.M, "Index out of bounds"
        assert hasattr(self, "_values"), "Values have not been assigned yet"
        return self._values[index]

    def values(self): 
        """Returns the values assigned to the samples
        
        Returns:
            numpy.ndarray: The values assigned to the samples
            
        Raises:
            AttributeError: If the values have not been assigned yet
        """
        assert hasattr(self, "_values"), "Values have not been assigned yet"
        return self._values
    
    def index(self, sample : np.ndarray):
        """ Returns the index of the given sample in the sampling array
        
        Args:
            sample (numpy.ndarray): The sample
            
        Returns:
            int: The index of the sample in the sampling array
            
        Raises:
            AssertionError: If the sample has the wrong shape
            AssertionError: If the sample is not in the sampling array
        """
        assert sample.shape == (self.m,), "Sample has wrong shape"
        assert sample in self._array, "Sample is not in the sampling array"
        return np.where(self._array == sample)[0][0]
    
    def save(self, filename : str):
        """Saves the sampling object to a json file

        Saves the sampling object to a json file. The file is saved in the current working directory.

        Args:
            filename (str): Name of the file to be saved

        Raises:
            TypeError: If the filename is not a string
        """
        assert isinstance(filename, str), "Filename must be a string"
        with open(filename, "w") as f:
            json.dump(self.__dict__, f, cls=NumpyEncoder, indent = 3)

    def load(self, data : dict, overwrite = False):
        """Loads array data into the sampling object

        Loads array data from dictionary into the sampling object. The array must have the shape (M,m) where M is the number of samples
        and m is the dimension of the parameter space.

        Args:
            data (dict): Dictionary containing numpy.ndarray data
            overwrite (bool, optional): If True, overwrites the existing samples. Default is False.

        Raises:
            AssertionError: If the array has the wrong shape


        """
        array = np.asarray(data["_array"])
        assert array.shape == (self.M, self.m), "Array has wrong shape"
        if not hasattr(self, "_array") or overwrite:
            self._array = array
            if "_values" in data:
                self._values = np.asarray(data["_values"])
        else:
            raise AttributeError("Samples already exist. Use overwrite=True to overwrite them")

class clustering(sampling):
    """Class for creating clustered samples of a parameter space as a subclass of sampling

    This class produces as sampling object that contains clustered samples of a parameter space in addition
    to the unclustered data. The clustering is done using the k-means algorithm.

    Attributes:
    public:
        M (int): Number of samples
        m (int): Dimension of the parameter space
        k (int): Number of clusters
    private:
        _array (numpy.ndarray): Array containing the samples
        _max_iter (int): Maximum number of iterations for the k-means algorithm
        _centroids (numpy.ndarray): Array containing the centroids of the clusters
        _clusters (list): List of index lists of each clusters

    Methods:
    public:
        detect(): Detects the clusters
        assign_clusters(data : numpy.ndarray) -> list: Assigns the samples to the clusters
        update_centroids(clusters : list): Updates the centroids of the clusters
        plot(filename : str): Plots the clusters
        clusters() -> list: Returns the clusters
        centroids() -> numpy.ndarray: Returns the centroids of the clusters
        cluster_index(x : numpy.ndarray) -> int: Returns the index of the cluster the sample belongs to

    Example:
        >>> kmeans = clustering(100, 2, 5)
        >>> kmeans.detect()
        >>> kmeans.plot("2D.pdf")

    Version:
        0.1
    Contributors:
        Niklas Hornischer (nh605@cam.ac.uk)
    """
    def __init__(self, M : int, m : int,  k : int, max_iter = 1000):
        """Constructor of the clustering object

        Args:
            M (int): Number of samples
            m (int): Dimension of the parameter space
            k (int): Number of clusters
            max_iter (int, optional): Maximum number of iterations for the k-means algorithm. Default is 1000.
        
        Raises:
            AssertionError: If k is not greater than 0 and less than M
        """
        assert 0 < k < M, "Number of clusters must be greater than 0 and less than the number of samples"
        super().__init__(M, m)
        self.object_type = "clustering"
        self.k = k
        self._max_iter = max_iter
    
    def detect(self):
        """
        Detects the clusters using the k-means algorithm
        """
        _min, _max = np.min(self._array), np.max(self._array)
        self._centroids = np.random.uniform(_min, _max, (self.k, self.m))
        _prev_centroids=None
        _iter=0
        while np.not_equal(self._centroids, _prev_centroids).any() and _iter < self._max_iter:
            _prev_centroids = self._centroids.copy()
            _clusters = self.assign_clusters(self._array)
            self.update_centroids(_clusters)
            _iter += 1
        self._clusters = _clusters
    
    def clusters(self):
        """Returns the clusters

        Returns:
            list: List of cluster containing a list of the indices of the samples belonging to the clusters
        """
        return self._clusters
    
    def centroids(self):
        """Returns the centroids of the clusters

        Returns:
            numpy.ndarray: Array containing the centroids of the clusters
        """
        return self._centroids

    def assign_clusters(self, data : np.ndarray):
        """Assigns the samples to the clusters

        This method can be used to assign samples to the clusters and is called by the detect method.
        It is possible to assign a arbitrary data set to the defined clusters, but in this case the sample space
        is not updated.
        
        Args:
            data (numpy.ndarray): Array containing the samples
        
        Returns:
            List: List of the clusters containing a list of the indices of the samples belonging to the clusters

        Raises:
            AssertionError: If the centroids have not been initialized or the dimension of the data does not match the dimension of the parameter space
        """
        assert hasattr(self, "_centroids"), "Centroids have not been initialized"
        assert np.shape(data)[1] == self.m, "Dimension of data does not match dimension of parameter space"
        _clusters=[[] for _ in range(self.k)]
        for i,x in enumerate(data):
            idx = self.cluster_index(x)
            _clusters[idx].append(i)
        return _clusters

    def cluster_index(self, x : np.ndarray):
        """Returns the index of the cluster to which the sample belongs

        Args:
            x (numpy.ndarray): Sample to be assigned to a cluster

        Returns:
            int: Index of the cluster to which the sample belongs

        Raises:
            AssertionError: If the centroids have not been initialized
            AssertionError: If the dimension of the data does not match the dimension of the parameter space
        """
        assert hasattr(self, "_centroids"), "Centroids have not been initialized"
        assert np.shape(x)[0] == self.m, "Dimension of data does not match dimension of parameter space"
        distances = np.linalg.norm(self._centroids-x, axis=1)
        cluster_idx = np.argmin(distances)
        return cluster_idx

    def update_centroids(self, _clusters : list):
        """Updates the centroids of the clusters

        This method can be used to update the centroids of the clusters and is called by the detect method.
        It is not recommended to use this method on its own, as it does not assign the samples to the clusters,
        but changes the centroids of the cluster.

        Args:
            _clusters (list): List of clusters of lists containing the indices of the samples belonging to the clusters
        """
        for i, centroid in enumerate(self._centroids):
            cluster_data = np.asarray([self.extract(idx) for idx in _clusters[i]])
            _new_centroid = np.mean(cluster_data, axis=0)
            if not np.isnan(centroid).any():
                self._centroids[i] = _new_centroid
    
    def plot(self, filename = "kmeans.pdf"):
        """Plots the clusters in the parameter space
        
        To visualize the figures, use plt.show() after calling this method. 
        This is especially useful when plotting 3D parameter spaces.

        Args:
            filename (str, optional): Name of the file to save the plot to. Default is kmeans.pdf
        
        Raises:
            AssertionError: If the dimension of the parameter space is greater than 3
        """
        import os
        import matplotlib.pyplot as plt
        from matplotlib import colors
        from matplotlib import cm
        dir = os.path.dirname(__file__)
        cmap = plt.get_cmap('hsv')
        scalarMap = cm.ScalarMappable(colors.Normalize(vmin=0, vmax=self.k),cmap=cmap)
        cluster_data = [np.asarray([self.extract(idx) for idx in self._clusters[i]]) for i in range(self.k)]
        if self.m == 1:
            plt.figure("K-means clustering (1D)")
            for i in range(self.k):
                plt.plot(self._centroids[i,0], 0, 'x', color=scalarMap.to_rgba(i))
                plt.scatter(cluster_data[i][:,0], np.zeros(cluster_data[i].shape[0]),color=scalarMap.to_rgba(i))
            plt.xlabel(r'$x_1$')
        elif self.m == 2:
            plt.figure("K-means clustering (2D)")
            for i in range(self.k):
                plt.plot(self._centroids[i,0], self._centroids[i,1], 'x', color=scalarMap.to_rgba(i))
                plt.scatter(cluster_data[i][:,0], cluster_data[i][:,1],color=scalarMap.to_rgba(i))
            plt.xlabel(r'$x_1$')
            plt.ylabel(r'$x_2$')
        elif self.m ==3:
            plt.figure("K-means clustering (3D)")
            ax = plt.axes(projection='3d')
            for i in range(self.k):
                ax.scatter3D(cluster_data[i][:,0], cluster_data[i][:,1], cluster_data[i][:,2],color=scalarMap.to_rgba(i))
                ax.scatter3D(self._centroids[i,0], self._centroids[i,1], self._centroids[i,2], marker='x',color=scalarMap.to_rgba(i))
            ax.set_xlabel(r'$x_1$')
            ax.set_ylabel(r'$x_2$')
            ax.set_zlabel(r'$x_3$')
        else:
            raise ValueError("Cannot plot more than 3 dimensions")
        plt.savefig(filename, dpi=300, format="pdf")

    def load(self, data : dict, overwrite = False):
        """
        Loads the data into the clustering object
        
        Args:
            data (numpy.ndarray): Data to be loaded into the clustering object
            centroids (numpy.ndarray): Centroids of the clusters
            clusters (list): List of clusters of lists containing the indices of the samples belonging to the clusters
            overwrite (bool, optional): If True, the data will be overwritten. Default is False
        
        Raises:
            ValueError: If the centroids have already been initialized and overwrite is False
            ValueError: If the clusters have already been initialized and overwrite is False
            
        """
        super().load(data, overwrite=True)
        if hasattr(self, "_centroids") and not overwrite:
            raise ValueError("Centroids have already been initialized. Set overwrite=True to overwrite the data.")
        else:
            self._centroids = np.asarray(data["_centroids"])
        if hasattr(self, "_clusters") and not overwrite:
            raise ValueError("Clusters have already been initialized. Set overwrite=True to overwrite the data.")
        else:
            self._clusters = []
            clusters = data["_clusters"]
            for i in range(len(clusters)):
                self._clusters.append(np.asarray(clusters[i]))
