#!/bin/bash

# Copyright Keith Butler(2014) #
# #
# This file NewPotentialModule.py is free software: you can #
# redistribute it and/or modify it under the terms of the GNU General Public #
# License as published by the Free Software Foundation, either version 3 of #
# the License, or (at your option) any later version. #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for #
# more details. #
# You should have received a copy of the GNU General Public License along with #
# this program. If not, see <http://www.gnu.org/licenses/>. #
# #
################################################################################

import numpy
import numpy as np
import math
from scipy import interpolate

#------------------------------------------------------------------------------------------
def match_extrema(A,B,centre_A,centre_B):
    """For refined matching of the centres of the two densities. The centre is always at an extreme, otherwise the density is asymmetric. Therefore finding the offset and shifting the projected bulk by this offset will result in symmetry.
    Args:
	A/B : 2D arrays of the potential
	centre_A/B : The indices of the central points
    Returns:
	offset : real number, the difference in extremum position
    """
# Find numerical values of maxima and minima
    min_A = min(A[centre_A-400:centre_A+400,1])
    max_A = max(A[centre_A-400:centre_A+400,1])
    min_B = min(B[centre_B-400:centre_B+400,1])
    max_B = max(B[centre_B-400:centre_B+400,1])

# Is is a minimum or a maximum?
    is_minimum = False
    if max_A == A[centre_A-400,0] or max_A == A[centre_A+400,0]:
	is_minimum = True
	print "It's a minimum"
    else:
	print "It's a maximum"
# Get the abscissa values corresponding to minima/maxima
    if is_minimum == True:
  	for i in range(centre_A-400,centre_A+400):
		if A[i,1] == min_A:
		    ext_A = A[i,0]
  	for i in range(centre_B-400,centre_B+400):
		if B[i,1] == min_B:
		    ext_B = B[i,0]
    else:
  	for i in range(centre_A-400,centre_A+400):
		if A[i,1] == max_A:
		    ext_A = A[i,0]
  	for i in range(centre_B-400,centre_B+400):
		if B[i,1] == max_B:
		    ext_B = B[i,0]

    print "Extrema points: ", ext_A,ext_B
    offset = ext_B - ext_A
    print "Offset: ",offset
    return offset

#------------------------------------------------------------------------------------------
def centre_of_charge(density,tol=0.001):
    """ Finds the centre point of a charge density in a slab geometry.
    NB : currently this cannot deal with a charge which crosses a periodic
    boundary, the density should be translated before applying.
    TODO(KTB): Adaapt for periodic boundaries.
    Args:
	density : 2D array of the charge density
    Returns
	centre  : real number, the centre of the density
    """
    in_slab = False
    print "---------------------------------"
    print "Searching for slab centre."
    print "---------------------------------"
    print "Length of slab",len(density)
    for point in density:
	if in_slab == False and point[1] > tol:
	    start = point[0]
	    in_slab = True
	if in_slab == True and point[1] < tol:
	    	end = point[0]
		in_slab = False
    mid_point = (start + end)/2
    print "CENTRE OF CAHRGE: ", mid_point
    return mid_point



#------------------------------------------------------------------------------------------
def gradient_magnitude(gx,gy,gz):
    """Converts the separate gradient magnitudes to a single magnitude
    Args:
        gx/y/z : fields in x y and z directions 2D array
    Returns:
        grad_mag : gradient of fields at each point"""

    grad_mag = gx
    for i in range(gx.shape[0]):
        for j in range(gy.shape[1]):
            for k in range(gz.shape[2]):
                grad_mag[i,j,k] = np.sqrt(gx[i,j,k]**2+gy[i,j,k]**2+gz[i,j,k]**2)

    return grad_mag
#------------------------------------------------------------------------------------------
def vector_2_abscissa(vector,magnitude,dx,dy,dz):
    """Converts a vactor with a magnitude given in units of grid density (NGX/Y/Z) to
    AA for plotting
    Args:
        vector : the vector along which the line is being plotted [(3x1) array]
        magnitude : the number of steps that were taken along that vector [Integer]
        dx/y/z: the resolution of the density grid in AA-1 [Real]
    Returns:
        abscissa : the values for plotting on the abscissa in AA [1D array]
    """
    vec_angs = [vector[0]*dx, vector[1]*dy, vector[2]*dz]
    vec_mag = np.linalg.norm(vec_angs)
    abscissa = np.zeros(shape=(magnitude))
    for i in range(magnitude):
        abscissa[i] = i*vec_mag

    return abscissa
#------------------------------------------------------------------------------------------
def number_in_field(gradients,cutoff):
    """Get the number of grid elements with a field magnitude greater than cutoff
    Args:
	gradients: the grid of field gradients (Real(ngx,ngy,ngz))
	cutoff: the value above which tocout them (Real)
    Returns:
	number_of_elements: the number satisfying the condition (Integer)
    """  
    number_of_elements = 0
    for element in np.nditer(gradients):	
	if element >= cutoff:
	    number_of_elements += 1
    
    return number_of_elements
#------------------------------------------------------------------------------------------
def element_vol(vol,nx,ny,nz):
    """Calculates the volume of each of the elements on the grid.
    Args:
	vol: the cell volume (real)
        x : the number of grid points in each direction (real)
    Returns:
	ele_vol : the volume (real)
    """

    number_of_elements = nx*ny*nz
    ele_vol = vol/number_of_elements

    return ele_vol

#------------------------------------------------------------------------------------------
def subs_potentials(A,B,tol):
    """Difference between two sets of data of the same length
    Args:
	A/B: the arrays (2D)
  	tol: the tolerence of the difference
    Returns:
	C: a new aaray (2D)
    """
    print "---------------------------------"
    print "Subtracting potentials.          "
    print "---------------------------------"

    C = A
    run_sum = 0
    for i in range(len(A)):
    	C[i,0] = A[i,0]
    	#if abs(A[i,1] - B[i,1]) <= tol:
        #    C[i,1] = 0
    	#else:
        C[i,1] = A[i,1] - B[i,1]
        run_sum = run_sum + (A[i,1] - B[i,1])

    print "Sum from difference routine: ", run_sum
    return C

#------------------------------------------------------------------------------------------
def bulk_vac(bulk, slab):
    """ This sets the electron density to zero in the regions of the projected 'bulk' which correspond to the vacuum region of the slab calculation.
    Args:
	bulk : 2D array.
	vacuum : 2D array.
    Returns:
	new_bulk : 2D array with vacuum zeros included.""" 
    new_bulk = np.zeros(shape=(len(slab),2))
    print "Adding vacuum to unoccupied regions"
    print "---------------------------------"
    i = -1
    for s_pot in slab:
	i = i + 1
	found = False
	for j in range(len(bulk)):
	    if s_pot[0] <= bulk[j,0] and s_pot[0] > bulk[j-1,0]:
		new_bulk[i,:] = bulk[j,:]
		found = True
     	if found == False:
	    new_bulk[i,0] = s_pot[0]
	    new_bulk[i,1] = 0

    return new_bulk
#------------------------------------------------------------------------------------------
def one_2_2d(Array,resolution,vector):
    """Converts the 1d potential array to 2D with angstroms in A[0]
    Args:
    	Array: 1D array
	resolution: density of sampling of distance (1/AA)
	vector: The vector of the direction of sampling
    Returns
	New_array: 2D array
    """
    length = np.sqrt(vector.dot(vector))
    New_array = np.zeros(shape=(len(Array)-1,2))
    resolution = length/len(Array)
    for i in range(len(Array)-1):
	New_array[i,0] = i*resolution
	New_array[i,1] = Array[i]
    
    return New_array
#------------------------------------------------------------------------------------------

def match_resolution(A,B):
    """Match the resolutions of two data-sets, given their range
    Args:
	A/B: two 2D arrays
    Returns:
	A_new/B_new : two new 2D arrays
    """

    np.append(A,A[0,:])
    np.append(B,B[0,:])
    resolution_a = (max(A[:,0])-min(A[:,0]))/len(A)
    resolution_b = (max(B[:,0])-min(B[:,0]))/len(B)
    new_resolution = min(resolution_a,resolution_b)/3
# Generate the function f for each spline
    f_a = interpolate.interp1d(A[:,0],A[:,1],kind='cubic')
    f_b = interpolate.interp1d(B[:,0],B[:,1],kind='cubic')
# Generate the new abscissa values, at new_resolution
    abscissa_a = np.arange(0,max(A[:,0]),new_resolution)
    abscissa_b = np.arange(0,max(B[:,0]),new_resolution)
# New datasets
    A_new = np.zeros(shape=(len(abscissa_a),2))
    B_new = np.zeros(shape=(len(abscissa_b),2))
    A_new[:,0] = abscissa_a
    B_new[:,0] = abscissa_b
    A_new[:,1] = f_a(abscissa_a)
    B_new[:,1] = f_b(abscissa_b)

    return A_new,B_new

#------------------------------------------------------------------------------------------
def c_spline_generate(A,new_res_factor):
    """Generate a spline of the data in a 2D array
    Args:
	A: 2D array
	new_res_factor: the factor by which to scale the resolution
    Returns:
	B: A spline of the data
    """
    resolution = (A[len(A)-1,0]-A[0,0])*new_res_factor/len(A)
    array_a = np.arange(min(A[:,0]),max(A[:,0]),resolution)
    f_a = interpolate.interp1d(A[:,0],A[:,1],kind='cubic')
    #ius = interpolate.InterpolatedUnivariateSpline(A[:,0],A[:,1])
    S = f_a(array_a)
    B = np.zeros(shape=(len(A)/new_res_factor,2))
    for i in range(len(B)):
    	B[i,0] = i*resolution+A[0,0]
    	B[i,1] = S[i]

    return B
#------------------------------------------------------------------------------------------
def matched_spline_generate(A,B):
    """Make sure the limits of two sets of data are the same with a splining
    Args:
	A/B: 2D array
    Returns:
	C/D: A spline of the data
    """
    print "---------------------------------"
    print "Matching limits of potentials"
    print "---------------------------------"
#   Decide which ranges to use
    lower_b = max(min(A[:,0]),min(B[:,0]))
    upper_b = min(max(A[:,0]),max(B[:,0]))
    resolution = (A[len(A)-1,0]-A[0,0])/len(A)
    array_a = np.arange(lower_b,upper_b,resolution)
      



    print "Generating function B."	
    f_a = interpolate.interp1d(A[:,0],A[:,1],kind='cubic')
    print "Generating function A."	
    f_b = interpolate.interp1d(B[:,0],B[:,1],kind='cubic')
    S = f_a(array_a)
    K = f_b(array_a)
    C = np.zeros(shape=(len(array_a),2))
    D = np.zeros(shape=(len(array_a),2))
    print "Splines generated, populating" 
    for i in range(len(B)):
    	C[i,0] = i*resolution+A[0,0]
    	C[i,1] = S[i]
    	D[i,0] = i*resolution+A[0,0]
    	D[i,1] = K[i]
    print "---------------------------------"

    return C,D
#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------
def spline_generate(A,new_res_factor):
    """Generate a spline of the data in a 2D array
    Args:
	A: 2D array
	new_res_factor: the factor by which to scale the resolution
    Returns:
	B: A spline of the data
    """
    resolution = (A[len(A)-1,0]-A[0,0])*new_res_factor/len(A)
    array_a = np.arange(min(A[:,0]),max(A[:,0]),resolution)
    print "Generating function A."	
    f_a = interpolate.interp1d(A[:,0],A[:,1],kind='slinear')
    print "Function generated."
    #ius = interpolate.InterpolatedUnivariateSpline(A[:,0],A[:,1])
    S = f_a(array_a)
    B = np.zeros(shape=(len(A)/new_res_factor,2))
    for i in range(len(B)):
    	B[i,0] = i*resolution+A[0,0]
    	B[i,1] = S[i]

    return B
#------------------------------------------------------------------------------------------

def matched_2d_spline_generate(A,B, V_A, V_B):
    """Create 2D splines of 2 datasets, with an x-axis of units AA
    Args:
	A/B: The two datasets to match up 1-D arrays.
	V_A/B: The vectors of the direction of plotting.
    Returns:
	A/B_new : the new 2D Splined datasets.
    """

# Convert vectors to magnitude
    length_A = np.sqrt(V_A.dot(V_A))
    length_B = np.sqrt(V_B.dot(V_B))
# Determine the new resolution to plot at; twice the highest existing resolution
    res_a = length_A/(len(A))
    res_b = length_B/(len(B))
    new_resolution = (min(res_a,res_b))
# Create an array containing the indices of each potential point 0,1,2,....N
    array_a = np.arange(0,len(A))
    array_b = np.arange(0,len(B))
# Generate the function f for each spline
    f_a = interpolate.interp1d(array_a,A,kind='cubic')
    f_b = interpolate.interp1d(array_b,B,kind='cubic')
# Generate new arrays with the same resolution
    limits_a_new = np.arange(0,len(A))
    limits_b_new = np.arange(0,len(B))
# Make the arrays
    A_new = f_a(limits_a_new)
    B_new = f_b(limits_b_new)
# Convert to 2D arrays with AA in the first column
    TD_A = np.zeros(shape=(len(A_new),2))
    TD_B = np.zeros(shape=(len(B_new),2))
    res_a = length_A/float(len(A_new))
    res_b = length_B/float(len(B_new))
    for i in range(len(A_new)):
	TD_A[i,1] = A[i]
	TD_A[i,0] = i*res_a
    for i in range(len(B_new)):
	TD_B[i,1] = B[i]
	TD_B[i,0] = i*res_b
    return TD_A, TD_B

#------------------------------------------------------------------------------------------
def scissors_shift(potential,delta):
    """Scissors shifts a full potential by delta
    Args:
	potential: a 2D array
	delta: a real number
    Returns:
	shifted_potential: a 2D array
    """
    shifted_potential = potential
    for i in range(len(potential)):
	shifted_potential[i,0] = potential[i,0]
	shifted_potential[i,1] = potential[i,1] - delta

    return shifted_potential

#------------------------------------------------------------------------------------------
def symmetric_extend_potential(potential,extension):
    """Symmetrically exted the potential in space, i.e. the same amount in +/- directions
    Args:
        potential: 2D array, the potential to be expanded.
        extension: integer, the number of times to extend the potential.
    Returns:
        extended_potential: the 2D array, extended n times

    The new potential looks like ------****++++++
    Where -/+ are the extensions and * is the original
    """

    length_new_array = extension*len(potential)
    new_potential = np.zeros(shape=(length_new_array,2))
    exten = (float(extension)-1)/2
    increment = potential[1,0] - potential[0,0]
    dist = exten*len(potential)      # The distance in each direction to extend.
    for i in range(len(new_potential)):
        index = i - dist - len(potential)*round((i-dist)/len(potential),0) # M.I.C.
        new_potential[i,0] = (i-dist)*increment
        new_potential[i,1] = potential[int(index),1]
	
    return new_potential

#------------------------------------------------------------------------------------------
def extend_potential(potential,extension,vector):
    """Takes a potential and expands it.
    Args:
   	potential: 2D array, the potential to be expanded.
	extension: integer, the number of times to extend the potential.
 	vector: 1D array, the vector along which you re epanding.
    Returns:
	extended_potential: the 2D array, extended n times"""
    extended_potential = np.zeros(shape=(int(extension*len(potential)),2))
    idx = 0
    diff = np.sqrt(vector.dot(vector))
    increment = diff/len(potential[:,0])
    for i in range(int(extension)):
	for j in range(len(potential)):
    	    extended_potential[idx,0]=potential[j,0]+i*diff
	    extended_potential[idx,1] = potential[j,1]
	    idx = idx + 1

    if int(extension) != extension:            # For non-integer extensions
	i = i + 1
	over_shoot = extension - int(extension) 
	for j in range(int(len(potential)*over_shoot)):
   	    extended_potential[idx,0]=potential[j,0]+i*(max(potential[:,0])-min(potential[:,0]))+increment*i
	    extended_potential[idx,1] = potential[j,1]
            idx = idx + 1

    return extended_potential
#------------------------------------------------------------------------------------------
def sort_potential(potential):
    """I had to write my own method to sort a 2D arry by the first row...I don't know why
    Args:
 	potential: 2-D array.
    Returns:
	sorted_potential the same array sorted by the first column.
    """

    idx = sorted(potential[:,0])
    sorted_potential = potential.copy()
    for i in range(len(idx)):
        for j in range(len(potential)):
            if potential[j,0] == idx[i]:
                sorted_potential[i,0] = idx[i]
                sorted_potential[i,1] = potential[j,1]

    return sorted_potential
#------------------------------------------------------------------------------------------
def diff_potentials(potential_a, potential_b,start,end,tol=0.04):
    """ Gets the difference betweeen two potentials, returns a 1D array
    Args:
   	potential_a/b: 2D arrays
	start/end : the start and finish coordinates 
	tol : the tolerence for the coordinated being the same for subtraction
    Returns:
	new_potential: 2D array
    """
    resolution = potential_a[0,0] - potential_b[0,1]
    new_potential = np.zeros(shape=((start-end)/resolution,2))
    
    for i in range(len(potential_a)):
	if potential_a[i,0] >= start and potential_a[i,0] <= end:
	    for j in range(len(potential_b)):
		if abs(potential_b[j,0] - potential_a[i,0]) <= tol:
	    	    new_potential[i,1] = potential_a[i,1] - potential_b[i,1]
	    	    new_potential[i,0] = potential_a[i,0]	
	    

    return new_potential
#------------------------------------------------------------------------------------------
def translate_grid(potential, translation, periodic=False, vector=[0,0,0],boundary_shift=0.0):
    """Move the potential around, useful for overlapping two plots, or
    shifting a slab to the centre of the plot, this works if periodic=True

    The new index in the potential arrays [:,0] gives a coordinate in grid points.
    Args:
	potential : 2D array containig the electrostaticpotential/charge density
	translation : the distance to move it
	periodic : boolean, perform wrapping of coordinates
	vector: the vector along which you are transorming only required for periodic = True
	boundary_shift : real, number of AA to shift the location of the periodic boundary
    Returns:
	new_potential_trans : 2D array containig the translated electrostaticpotential/charge density 
    """
    new_potential_trans = np.zeros((len(potential),2))
    new_potential_orig = np.zeros((len(potential),2))
    length = np.sqrt(vector.dot(vector))


    beginning = potential[0,0]
    for i in range(len(potential)):
    	new_potential_trans[i,0] = potential[i,0] + translation
	new_potential_trans[i,1] = potential[i,1]
        if periodic == True:
	    new_potential_trans[i,0] = new_potential_trans[i,0] - length*int((new_potential_trans[i,0]+boundary_shift)/(length+beginning))

    if periodic == True:
# Sort the numbers out if you have done periodic wrapping
    	sorted_potential_trans = sort_potential(new_potential_trans)
    else:
	sorted_potential_trans = new_potential_trans

    #print sorted_potential_trans

    return sorted_potential_trans

#------------------------------------------------------------------------------------------
def get_periodicity(A):
    """Gets the periodicity of a 2D array
    Args:
	A : 2D array
    Returns:
	period : real number; abscissa periodicity
    """

    print "---------------------------------"
    print "Finding periodicity routine"
    print "---------------------------------"
    minima = []
    minima_abscissa = []
    separation = []
    for i in range(1,len(A)-1):
	if A[i-1,1] < A[i,1] and A[i+1,1] < A[i,1]:
   	    minima.append(round(A[i,1],4))
	    minima_abscissa.append(A[i,0])
    for i in range(len(minima)):
	found_next = False
	for j in range(i+1,len(minima)):
		if minima[i] == minima[j] and found_next == False:
		    found_next = True
		    separation.append(minima_abscissa[j] - minima_abscissa[i])

    period = numpy.average(separation)
    return period
#------------------------------------------------------------------------------------------

def macroscopic_average(potential,periodicity,resolution):
    """Getting the macroscopic average of potential
    Args:
         potential : 2D array containig the electrostaticpotential/charge density
	 periodicity : real number; the period over which to average
	 resolution : the grid resolution in the direction of averaging
    Returns:
	 macro_average : array with the macroscopically averaged values"""

    print "---------------------------------"
    print "MacroScopic averaging routine    "
    print "---------------------------------"
    macro_average = np.zeros(shape=(len(potential),2))
    period_points = int((periodicity/resolution))
# Re-arrange so that period points divides evenly by resolution
    for i in range(len(potential)):
	for j in range(i-int(period_points/2),i+int(period_points/2)):
	    if j < 0:
	    	macro_average[i,1] = macro_average[i,1]+potential[j+len(potential),1]
	    elif j >= len(potential):
	    	macro_average[i,1] = macro_average[i,1]+potential[j-len(potential),1]
	    else:
	    	macro_average[i,1] = macro_average[i,1]+potential[j,1]
	macro_average[i,1] = macro_average[i,1]/period_points
	macro_average[i,0] = potential[i,0]

    print ("Average of the average = ",numpy.average(macro_average))
    return macro_average

def cube_potential(origin,travelled,cube,Grid,nx,ny,nz):
    """Populates the sampling cube with the potential required"""

# Recalc the origin as grid point coordinates
    n_origin = np.zeros(shape=(3))
    n_origin[0] = int(origin[0]*nx)
    n_origin[1] = int(origin[1]*ny)
    n_origin[2] = int(origin[2]*nz)
    potential_cube = np.zeros(shape=(cube[0],cube[1],cube[2]))
    for x in range(0,cube[0]):
        for y in range(0,cube[1]):
    	    for z in range(0,cube[2]):
# Assign the values of coordinates in the original grid
		xv = n_origin[0]+travelled[0]+x
		yv = n_origin[1]+travelled[1]+y
		zv = n_origin[2]+travelled[2]+z
# Minimum image convention
	    	zv = zv - nz*round(zv/nz)
	    	yv = yv - ny*round(yv/ny)
	    	xv = xv - nx*round(xv/nx)
        	potential_cube[x,y,z] = Grid[xv,yv,zv]

    return potential_cube.mean(), np.var(potential_cube)
#------------------------------------------------------------------------------------------

def cuboid_average(Grid,cube,origin,vector,nx,ny,nz,magnitude):
   """Calculates the average in a cube defined by size cube(a,b,c), beginning at origin and 
    reavelling as far as magnitude."""

   plotting_average = np.zeros(shape=(magnitude))
   i = 0
   while i < magnitude:
 	travelled = np.multiply(i, vector) 
    	plotting_average[i], varience = cube_potential(origin,travelled,cube,Grid,nx,ny,nz)
	i = i + 1

   return plotting_average 
#------------------------------------------------------------------------------------------

def planar_average(Grid,nx,ny,nz):
    """Calculate the average in a given plane for the full length of the normal;
    e.g. the full length of z in the xy plane."""
    axis = raw_input("Which axis do you wish to plot along?(x,y,z)LOWER CASE!! ")
    if axis == 'x':
	x_plane = np.zeros(shape=(ny,nz))
	Average = np.zeros(shape=(nx))
        for x_value in range(nx):
	    x_plane[:,:] = Grid[x_value,:,:]
            Average[x_value] = x_plane.mean()
    if axis == 'y':
	Average = np.zeros(shape=(ny))
	y_plane = np.zeros(shape=(nx,nz))
        for y_value in range(ny):
	    y_plane[:,:] = Grid[:,y_value,:]
            Average[y_value] = y_plane.mean()
    if axis == 'z':
	Average = np.zeros(shape=(nz))
	z_plane = np.zeros(shape=(nx,ny))
        for z_value in range(nz):
	    z_plane[:,:] = Grid[:,:,z_value]
            Average[z_value] = z_plane.mean()

    return Average
#------------------------------------------------------------------------------------------

def create_plotting_mesh(NGX,NGY,NGZ,plane_coeff,grad):
    """Create the mesh of points for a contour plot"""
    xx, yy = np.mgrid[0:NGX,0:NGY]
    x = 0
    grd = np.zeros(shape=(NGX,NGY))
    while x < NGX:
        y = 0
        while y < NGY:
            z = 0
            while z < NGZ:
                z_value = (plane_coeff[3]-plane_coeff[0]*x-plane_coeff[1]*y)/plane_coeff[2]
		while z_value >= NGZ-1:
		    z_value = z_value - NGZ
                grd[x,y] = grad[x,y,z_value]
                z = z + 1
            y = y + 1
        x = x + 1
    return xx,yy,grd
#------------------------------------------------------------------------------------------
def get_volume(a,b,c):
    """Calculate the volume of the cell from lattice vectors
    Args:
	a/b/c: vectors of the lattice edges
    """
    volume = np.dot(a,np.cross(b,c))

    return volume
#------------------------------------------------------------------------------------------

def numbers_2_grid(a,NGX,NGY,NGZ):
    """Takes a point (in fractional coordinates) and converts it to a VASP grid
    point based on the NGX/Y/Z values."""
    a_grid = np.zeros(shape=(3))
    a_grid[0] = round(float(a[0])*NGX)
    a_grid[1] = round(float(a[1])*NGY)
    a_grid[2] = round(float(a[2])*NGZ)

    return a_grid
#------------------------------------------------------------------------------------------

def matrix_2_abc(Lattice):
    """The the VASP lattice and convert to the a,b,c,alpha,beta,gamma format"""

    a = np.sqrt(Lattice[0,0]**2+Lattice[0,1]**2+Lattice[0,2]**2)
    b = np.sqrt(Lattice[1,0]**2+Lattice[1,1]**2+Lattice[1,2]**2)
    c = np.sqrt(Lattice[2,0]**2+Lattice[2,1]**2+Lattice[2,2]**2)

    a_vec = Lattice[0,:]
    b_vec = Lattice[1,:]
    c_vec = Lattice[2,:]

    return a,b,c,a_vec,b_vec,c_vec
#------------------------------------------------------------------------------------------

def read_vasp_density(FILE):
    """Generic reading of CHGCAR LOCPOT etc files from VASP"""
    f = open(FILE,"r")
    lines = f.readlines()
    f.close()
# Get Header information
    i = 0
    lattice = np.zeros(shape=(3,3))
    for line in lines:
     inp = line.split()
     if inp == []:
      continue
     if len(inp) > 0:
      i = i+1
     if i == 2:
      scale_factor = float(inp[0])
     if i >= 3 and i < 6:
      lattice[i-3,:]=inp[:]
     if i == 6:
      num_species=len(inp)
      species=inp
     if i == 7:
      num_type=inp
      j = 0
      while (j < num_species):
       num_type[j-1] = int(num_type[j-1])
       j = j + 1
      num_atoms=sum(num_type)
     if i == 8:
      coord_type = inp
    
    for i in range(2):
     for j in range(2):
      lattice[i,j] = lattice[i,j]*scale_factor
# Restart reading to get the coordinates...it's just easier this way!
    i=0
    Coordinates = numpy.zeros(shape=(num_atoms,3))
    for line in lines:
     inp = line.split()
     if len(inp) > 0:
      i = i + 1
     if i >= 9 and i <= num_atoms+8 and len(inp) > 0:
      Coordinates[i-9,0] = float(inp[0])
      Coordinates[i-9,1] = float(inp[1])
      Coordinates[i-9,2] = float(inp[2])
# Now get the info about the charge grid
    i = 0
    for line in lines:
     inp = line.split()
     if len(inp) > 0:
      i = i + 1
     if i == num_atoms + 9:
      NGX = int(inp[0])
      NGY = int(inp[1])
      NGZ = int(inp[2])
      k = 0
      Potential = numpy.zeros(shape=(NGX*NGY*NGZ))
# Read in the potential data
     if i > num_atoms + 9 and i < num_atoms + 10 + NGX*NGY*NGZ/5:
      Potential[k]   = inp[0]
      Potential[k+1] = inp[1]
      Potential[k+2] = inp[2]
      Potential[k+3] = inp[3]
      Potential[k+4] = inp[4]
      k = k + 5
      if math.fmod(k,100000) == 0:
       print "Reading potetial, at point", k

    print	"BBBB		OOOO		OOOO		MMMMM	"
    print	"BBBB		OOOO		OOOO		MMMMM	"
    print	"BBBB		OOOO		OOOO		MMMMM	"
    print	"B  B	        OOOO		OOOO		MMMMM	"
    print	"B  B	        O  O		O  O		MMMMM	"
    print	"B  B	        O  O		O  O		MMMMM	"
    print	"B  B	        O  O		O  O		MMMMM	"
    print	"B  B	        O  O		O  O		MMMMM	"
    print	"BBBB	        O  O            O  O		M M M	"
    print	"BBBB	        O  O		O  O		M M M	"
    print	"BBBB	        O  O		O  O		M M M	"
    print	"B  B	        O  O		O  O		M M M	"
    print	"B  B	        O  O		O  O		M M M	"
    print	"B  B	        O  O		O  O		M M M	"
    print	"B  B	        O  O		O  O		M M M	"
    print	"B  B	        OOOO    	OOOO		M M M	"
    print	"BBBB            OOOO	        OOOO		M M M	"
    print	"BBBB            OOOO	        OOOO		M M M	"
    print	"BBBB            OOOO	        OOOO		M M M	"
 

    print ("Average of the potential = ",numpy.average(Potential))
    f.close()
    return Potential, NGX, NGY, NGZ, lattice
#------------------------------------------------------------------------------------------
def density_2_grid(Density,nx,ny,nz,Charge=False,Volume=1):
    """Convert the Potetnial list to a grid for ease of manipulation
    Args:
   	Density: Array of the output from a VAsp calulation charge/potential
	nx,y,z : Number of mesh points in x/y/z
	Charge : Boolean, is it charge or potential (charge needs ot be normalised by vol)
	Volume : The lattice vectors, only required for normalising charge.
     Returns:
	Potential_grid: the (normalised) quantity on a mesh
	total_electrons : the number of electrons in the system
	"""
    l = 0   
    Potential_grid = np.zeros(shape=(nx,ny,nz))
    total_electrons = 0
    is_CHGCAR = True
    for k in range(nz):
	for j in range(ny):
	    for i in range(nx):
		Potential_grid[i,j,k] = Density[l]/Volume
 		if Charge == True:
# Convert the charge density to a number of electrons
		    point_volume = Volume/(nx*ny*nz)
		    Potential_grid[i,j,k] = Potential_grid[i,j,k]*point_volume
		total_electrons = total_electrons + Density[l]
		l = l + 1
    if Charge == True:
    	print "Total electrons: ", total_electrons/(nx*ny*nz)
    total_electrons = total_electrons/(nx*ny*nz)
    return Potential_grid,total_electrons
#------------------------------------------------------------------------------------------

def points_2_plane(a,b,c):
    """define a plane based on 3 points
       method as outlined on http://www.had2know.com/academics/equation-plane-through-3-points.html
    """

    coefficients = np.zeros(shape=(4))

    ca = c - a
    ba = b - a
    normal = np.cross(ca,ba)
    d = normal[0]*a[0] + normal[1]*a[1] + normal[2]*a[2]
    for i in 0, 1, 2:
	coefficients[i] = normal[i]
    coefficients[3] = d
    return coefficients 

#------------------------------------------------------------------------------------------
def get_third_coordinate(plane_coeff,NGX,NGY):
    """Given the two sides of a plane, calculate the values of the 'plane' based on the
       equation eariler """

    zz = []
    i = j = 0
    while i <= NGX:
	i = i + 1
	j = 0
	while j <= NGY:
	    j = j + 1
	    rounded = round(((plane_coeff[0]*j+plane_coeff[1]*i) / plane_coeff[2]))
	    standard = ((plane_coeff[0]*j+plane_coeff[1]*i)/plane_coeff[2])
 	    if rounded == standard:   # Is it a whole number?
		zz.append(-(plane_coeff[0]*i+plane_coeff[1]*j)/plane_coeff[2])

    return zz
	 
#------------------------------------------------------------------------------------------
def normalise_arrays(A,B):
    """Given 2 arrays A and B which should have the same total, but have some small difference due to numerical errors this normalises each element of A so that the numbers should match
    Args:
	A/B: 2D arrays
    Returns:
	A/B: 2D arrays
    """
    print "---------------------------------"
    print "Re-normalising arrays"
    print "---------------------------------"
# GET THE REQUIRED OFFSET
    A_total = 0
    B_total = 0
    interval = (A[1,0] - A[0,0])
    for element in A:
        A_total = A_total + element[1]*interval
    interval = B[1,0] - B[0,0]
    for element in B:
        B_total = B_total + element[1]*interval
# RE-EVALUATE THE BULK ON THE BASIS OF THE DIFFERENCE
    interval = A[1,0] - A[0,0]
    differences = B_total - A_total
    re_adjustment = differences/(len(A)*interval)
    print "Required shift: ", differences
    print "Shift per element: ", re_adjustment
    for i in range(len(A)):
        A[i,:] = A[i,:] + re_adjustment
# TEST THE PROCEDURE
    interval = (A[1,0] - A[0,0])
    A_total = 0
    B_total = 0
    print "INTERVAL: ",interval
    for element in A:
        A_total = A_total + element[1]*interval
    interval = B[1,0] - B[0,0]
    print "INTERVAL: ",interval
    for element in B:
        B_total = B_total + element[1]*interval
    if len(A) == len(B):
	running_diff = 0
        for i in range(len(A)):
   	    running_diff = running_diff + A[i,1]-B[i,1]
        print "Summed element differences: ", running_diff

    print "Resulting difference: ",B_total - A_total

    return A, B
#------------------------------------------------------------------------------------------
