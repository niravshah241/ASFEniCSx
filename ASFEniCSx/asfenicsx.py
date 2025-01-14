import numpy as np

from ASFEniCSx.utils import debug_info
from ASFEniCSx.sampling import Sampling
from ASFEniCSx.functional import Functional

class ASFEniCSx:
    """Class for constructing the active subspace in FeniCSx based on Constantine et al. 

    The class is based on the paper by Constantine et al. The class is constructed
    to be used with the FeniCSx library and requires a functional and a sampling object.
    It is important to know that the eigenvectors of the active subspace can be in the direction
    of positive impact on the cost function or negative impact. This is not known beforehand and
    is therefore not specified in the class. The user must therefore check the direction of the
    eigenvectors and change the sign if needed.

    Attributes:
    public:
        k (int): Number of eigenvalues of interest
        function (Functional): Functional describing the quantity of interest
        samples (Sampling): Sampling object containing the samples
        eigenvalues (numpy.ndarray): Eigenvalues of the covariance matrix (if created)
        eigenvectors (numpy.ndarray): Eigenvectors of the covariance matrix (if created)

    Methods:
    public:
        evaluate_gradients(info : bool, optional) : Evaluates the gradients of the function at the samples
        covariance(info : bool, optional): Approximates the covariance matrix of the gradient of the function
        estimation() : Performs the random sampling algorithm to construct the active subspace
        partition(n : int) : Partitions the active subspace into the active and inactive subspace
        bootstrap(n : int, info : bool, optional) : Performs the bootstrap algorithm to estimate the error
        calculate_eigenpairs(matrix : np.ndarray) : Calculates the eigenpairs of the given matrix
        plot_eigenvalues() : Plots the eigenvalues of the covariance matrix
        plot_subspace() : Plots distance of the active subspace using bootstrap
    Example:
        >>> from ASFEniCSx import ASFEniCSx, Sampling, Functional
        >>> def f(x): return x[0]**2 + x[1]**2
        >>> def dfdx(x): return [2*x[0], 2*x[1]]
        >>> samples = Sampling(100, 2)
        >>> function = Functional(2, f)
        >>> function.get_derivative(dfdx)                           # Optional but sets the derivative of the function to the analytical solution
        >>> asfenicsx = ASFEniCSx(1, function, samples)
        >>> U, S = asfenicsx.estimation()

    Version:
        0.1
    Contributors:
        Niklas Hornischer (nh605@cam.ac.uk)
    """

    def __init__(self, k : int, function : Functional, samples : Sampling, debug = True):
        """Constructor for the ASFEniCSx class

        Args:
            k (int): Number of eigenvalues of interest
            function (functional): functional describing the quantity of interest
            samples (sampling): sampling object containing the samples
            debug (bool, optional): If True, debug information is printed. Defaults to False.

        Raises:
            ValueError: If n is larger than the number of dimensions of the parameter space
        """
        assert k <= samples.m, "n must be smaller than the number of dimensions of the parameter space"
        self.k = k
        self.function = function
        self.samples = samples
        self._debug = debug

    def eigenvalues(self):
        """Returns the eigenvalues of the covariance matrix

        Returns:
            np.ndarray: Eigenvalues of the covariance matrix
        """
        if not hasattr(self, 'eigenvalues'):
            raise ValueError("Eigenvalues not calculated yet. Run the random sampling algorithm first.")
        return np.copy(self._eigenvalues)

    def evaluate_gradients(self, **kwargs):
        """Evaluates the gradients of the function at the samples

        Args:
            
        Returns:
            np.ndarray: Matrix containing the gradients of the function at the samples in the rows
        """

        # Check if additional arguments are given
        debug_info(self._debug, "Evaluating gradients for active subspace construction")
        gradients = np.zeros([self.samples.M, self.samples.m])
        for i in range(self.samples.M):
            gradients[i] = self.function.gradient(self.samples.extract(i), self.samples, **kwargs)
        self.gradients = gradients

        # Normalize the gradients accroding to the chain rule with the bounds from the sampling space to the range [-1, 1]
        if hasattr(self.samples, '_bounds'):
            for i in range(self.samples.M):
                for j in range(self.samples.m):
                    gradients[i,j] = gradients[i,j] * (self.samples._bounds[j,1] - self.samples._bounds[j,0]) / 2
        return gradients

    def covariance(self, gradients : np.ndarray):
        """Approximates the covariance matrix of the gradient of the function

        The calculation of the gradient is defined directly in the functional.
        The covariance matrix is approximated by the outer product of the gradient.
        
        Args:
            gradients (numpy.ndarray): Matrix containing the gradients of the function at the samples in the rows

        Returns:
            np.ndarray: Approximated covariance matrix with dimensions m x m    
        """
        covariance = np.zeros([self.samples.m, self.samples.m])
        for i in range(self.samples.M):
            covariance += np.outer(gradients[i,:], gradients[i,:])
        covariance = covariance / self.samples.M

        return covariance
    
    def estimation(self):
        """Calculates the active subspace using the random sampling algorithm of Constantine et al.
        Corresponds to Algorithm 3.1 in the book of Constantine et al.

        Args:
        
        Returns:
            np.ndarray: Matrix of eigenvectors stored in the columns
            np.ndarray: Vector of eigenvalues
        """

        # Evaluate the gradients of the function at the samples
        debug_info(self._debug, "Constructing the active subspace using the random sampling algorithm")
        if not hasattr(self, 'gradients'):
            debug_info(self._debug, "Evaluating gradients for active subspace construction")
            self.evaluate_gradients()
        else:
            print("WARNING: Gradients already evaluated, skipping evaluation. Make sure the gradients are up to date.")

        # Construct the covariance matrix
        convariance_matrix = self.covariance(self.gradients)

        # Calculate the eigenvalues and eigenvectors of the covariance matrix
        S, U = self.calculate_eigenpairs(convariance_matrix)

        self._eigenvalues = S
        self._eigenvectors = U

        debug_info(self._debug, f"Active subspace constructed")

        return (self._eigenvectors, self._eigenvalues)
    
    def partition(self, n : int):
        """Partitions the active subspace into two subspaces of dimension n and m-n

        Args:
            n (int): Dimension of the active subspace

        Returns:
            np.ndarray: Matrix containing the active subspace of dimension n
            np.ndarray: Matrix containing the inactive subspace of dimension m-n
        """
        # Check if the eigenvalues are already calculated
        if not hasattr(self, 'eigenvalues'):
            raise("Eigenvalues not calculated yet. Run the random sampling algorithm first.")

        # Check if the dimension of the active subspace is smaller than the dimension of the parameter space
        if n > self.samples.m:
            raise("Dimension of the active subspace must be smaller than the dimension of the parameter space.")

        W1 = self._eigenvectors[:,:n]
        W2 = self._eigenvectors[:,n:]
        self.W1 = W1
        return (W1, W2)
    
    def bootstrap(self, M_boot : int):
        """ Compute the bootstrap values for the eigenvalues
        
        Args:
            M_boot (int): Number of bootstrap samples
            
        Returns:
            np.ndarray: Bootstrap lower and upper bounds for the eigenvalues
            np.ndarray: Bootstrap lower and upper bounds for the subspace distances
        """
        if not hasattr(self, 'gradients'):
            self.evaluate_gradients()

        if not hasattr(self, 'eigenvalues'):
            self.estimation()

        # Loop over the number of bootstrap samples
        eigenvalues = np.zeros([self.samples.m, M_boot])
        subspace_distances = np.zeros([self.samples.m, M_boot])
        for i in range(M_boot):
            # Construct bootstrap replicate
            bootstrap_indices = np.random.randint(0, self.samples.M, size = self.samples.M)
            bootstrap_replicate = self.gradients[bootstrap_indices,:].copy()

            # Compute the bootstraped singular value decomposition
            S, U = self.calculate_eigenpairs(self.covariance(bootstrap_replicate))

            for j in range(self.samples.m-1):
                subspace_distances[j,i] = np.linalg.norm(np.dot(self._eigenvectors[:,:j+1].T, U[:,j+1:]), ord=2)
            eigenvalues[:,i] = S
        sub_max = np.max(subspace_distances, axis=1)
        sub_min = np.min(subspace_distances, axis=1)
        sub_mean = np.mean(subspace_distances, axis=1)

        # Compute the max and min of the eigenvalues over all bootstrap samples
        e_max = np.max(eigenvalues, axis=1)
        e_min = np.min(eigenvalues, axis=1)

        self.e_boot = [e_max, e_min]
        self.sub_boot = [sub_max, sub_min, sub_mean]

        debug_info(self._debug, f"Bootstrap values calculated")

        return [e_max, e_min], [sub_max, sub_min, sub_mean]
    
    def calculate_eigenpairs(self, matrix : np.ndarray):
        """Calculates the eigenvalues and eigenvectors of a matrix

        Args:
            matrix (np.ndarray): Matrix to calculate the eigenvalues and eigenvectors of

        Returns:
            np.ndarray: Vector of eigenvalues
            np.ndarray: Matrix of eigenvectors stored in the columns
        """
        e, W = np.linalg.eigh(matrix)
        e = abs(e)
        idx = e.argsort()[::-1]
        e = e[idx]
        W = W[:,idx]
        normalization = np.sign(W[0,:])
        normalization[normalization == 0] = 1
        W = W * normalization
        return e, W
    
    def plot_eigenvalues(self, filename = "eigenvalues.png", true_eigenvalues = None, ylim=None):
        """Plots the eigenvalues of the covariance matrix on a logarithmic scale

        Args:
            filename (str, optional): Filename of the plot. Defaults to "eigenvalues.png".
            true_eigenvalues (np.ndarray, optional): True eigenvalues of the covariance matrix. Defaults to None.
        Raises:
            ValueError: If the covariance matrix is not defined
        """
        if not hasattr(self, "_eigenvectors"):
            raise ValueError("Eigendecomposition of the covariance matrix is not defined. Calculate it first.")
        import matplotlib.pyplot as plt
        fig = plt.figure(filename)
        ax = fig.gca()
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        if true_eigenvalues is not None:
            ax.plot(range(1, self.k+1), true_eigenvalues[:self.k], marker="o", fillstyle="none", label="True")
        ax.plot(range(1, self.k+1), self._eigenvalues[:self.k], marker="x", fillstyle="none", label="Est")
        if hasattr(self, "e_boot"):
            debug_info(self._debug, "Plotting bootstrap bounds for eigenvalues")
            ax.fill_between(range(1, self.k+1), self.e_boot[0][:self.k], self.e_boot[1][:self.k], alpha=0.5, label = "BI")
        plt.yscale("log")
        plt.xlabel("Index")
        plt.ylabel("Eigenvalue")
        plt.legend()
        plt.grid()
        if ylim is not None:
            plt.ylim(ylim)
        plt.savefig(filename)
        plt.close()

    def plot_subspace(self, filename = "subspace", true_subspace = None, ylim=None):
        """Plots the subspace distances

        Args:
            filename (str, optional): Filename of the plot. Defaults to "subspace.png".
        Raises:
            ValueError: If the covariance matrix is not defined
        """
        if not hasattr(self, "_eigenvectors"):
            raise ValueError("Eigendecomposition of the covariance matrix is not defined. Calculate it first.")
        import matplotlib.pyplot as plt
        fig = plt.figure(filename)
        ax = fig.gca()
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        if true_subspace is not None:
            ax.plot(range(1, self.k), true_subspace[:self.k-1], marker="o", fillstyle="none", label="True")
        ax.plot(range(1, self.k), self.sub_boot[2][:self.k-1], marker="x", fillstyle="none", label="Est")
        if hasattr(self, "sub_boot"):
            debug_info(self._debug, "Plotting bootstrap bounds for subspace distances")
            ax.fill_between(range(1, self.k), self.sub_boot[0][:self.k-1], self.sub_boot[1][:self.k-1], alpha=0.5, label = "BI")
        plt.xlabel("Subspace Dimension")
        plt.yscale("log")
        plt.ylabel("Subspace Error")
        plt.legend()
        plt.grid()
        if ylim is not None:
            plt.ylim(ylim)
        plt.savefig(filename)
        plt.close()

    def plot_sufficient_summary(self, filename = "sufficient_summary"):

        # TODO: This looks strange
        # Compute the active variable values
        if not hasattr(self, "W1"):
            raise("The active subspace is not defined. If the eigenpairs of the covariance matrix are already calculated, call partition() first.")
        
        active_variable_values = self.samples.normalized_samples().dot(self.W1)
        if hasattr(self.samples, "_values"):
            values = self.samples.values()
        else:
            values = np.asarray([self.function.evaluate(self.samples.extract(i)) for i in range(self.samples.M)])

        n = active_variable_values.shape[1]
        import matplotlib.pyplot as plt

        for i in range(min(n, 2)):
            if n > 1:
                fig = plt.figure(filename + f"univariate_{i+1}")
            else:
                fig = plt.figure(filename + f"univariate")
            ax = fig.gca()
            ax.scatter(active_variable_values[:,i], values)
            if n > 1:
                plt.xlabel(f"Active Variable {i+1}")
            else:
                plt.xlabel("Active Variable")
            plt.ylabel("Function Value")
            plt.grid()
            if n > 1:
                plt.savefig(filename + f"univariate_{i+1}")
            else:
                plt.savefig(filename + f"univariate")
            plt.close()
        
        if n > 1 and n<=2:
            plt.figure(filename + f"bivariate")
            plt.axes().set_aspect('equal')
            plt.scatter(active_variable_values[:,0], active_variable_values[:,1], c=values, vmin=np.min(values), vmax=np.max(values) )
            plt.xlabel("Active Variable 1")
            plt.ylabel("Active Variable 2")
            ymin = 1.1*np.min([np.min(active_variable_values[:,0]) ,np.min( active_variable_values[:,1])])
            ymax = 1.1*np.max([np.max(active_variable_values[:,0]) ,np.max( active_variable_values[:,1])])
            plt.axis([ymin, ymax, ymin, ymax])    
            plt.grid()
            
            plt.colorbar()
            plt.savefig(filename + f"bivariate")
    
            plt.close()

    def plot_eigenvectors(self, filename = "eigenvectors.png", true_eigenvectors = None, n = None):
        """Plots the eigenvectors of the covariance matrix

        Args:
            filename (str, optional): Filename of the plot. Defaults to "eigenvectors.png".
            true_eigenvectors (np.ndarray, optional): True eigenvectors of the covariance matrix. Defaults to None.
        Raises:
            ValueError: If the covariance matrix is not defined
        """
        if n is None:
            n = self.k
        if not hasattr(self, "_eigenvectors"):
            raise ValueError("Eigendecomposition of the covariance matrix is not defined. Calculate it first.")
        import matplotlib.pyplot as plt
        fig = plt.figure(filename)
        ax = fig.gca()
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        for i in range(n):
            if true_eigenvectors is not None:
                ax.plot(range(1, self.k+1), true_eigenvectors[:,i], marker="o", fillstyle="none", label=f"True ({i+1}))")
            ax.plot(range(1, self.k+1), self._eigenvectors[:,i], marker="x", fillstyle="none", label=f"Est ({i+1})")
        plt.xlabel("Index")
        plt.ylim([-1,1])
        plt.ylabel("Eigenvector")
        plt.legend()
        plt.grid()
        plt.savefig(filename)
        plt.close()

# TODO: Check if private/protected variales are returned as objects or as copys.