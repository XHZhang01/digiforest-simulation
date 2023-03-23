from skimage import io
from http.server import executable
import random
from struct import pack
import rospy
import os
import roslaunch
import time
from geometry_msgs.msg import Pose
from gazebo_msgs.srv import SpawnModel, SpawnModelRequest
import argparse
import numpy as np
import scipy.stats as st
import subprocess
import cv2 as cv
import tqdm


def generate_heightmap(z_max: int)->np.array:
    """
    Function that generates an image heightmap
    :param z_max: value which indicates maximum value the heightmap can have
    """

    img = np.zeros([128, 128])

    for _ in tqdm.tqdm(range(1000)):
        
        x = random.randint(0, img.shape[0])
        y = random.randint(0, img.shape[0])
        update = obtain_normal_update([y, x], [[7, 0], [0, 7]], img.shape) * 20
        img += update 

    img = img - img.min()
    img = cv.GaussianBlur(img,(11,11),5)
    img = np.clip(img, 0, z_max)

    #img = img - img.min()


    return img


def obtain_normal_update(pos: list, cov: list, shape: list)->np.array:
    """
    Given a position and its covariance matrix, return the values for the gridded images we are working with
    :param pos: array with the [y, x] locations where the center of the normal function will be held
    :param cov: array of the covariance matrix that will tell the shape of the gaussian
    :param shape: array which contains the dimensions of the grid to update [y, x] format
    :return: numpy array with the values of the normal distribution accross the whole pixels of our depth images
    """

    x, y = np.mgrid[0:shape[1]:1, 0:shape[0]:1]
    grid = np.dstack((x, y))
    rv = st.multivariate_normal(pos, cov)
    map_update = rv.pdf(grid)

    return map_update





def get_position(cdf_array: np.array)->int:
    """
    Given a cdf, generate a random value between [0, 1] = B and compute the array position where
    P(X >= B)
    :param cdf_array: numpy array which is the cdf of a probability distribution
    """

    B = random.uniform(0, 1)

    for i in range(cdf_array.shape[0]):

        if cdf_array[i] > B:
            return i
    
    return cdf_array.shape[0] - 1


def next_position(probability_map, var = 3):
    """
    Procedure to generate random positioning of trees. Probability map has the probability of each pixel having a tree. The aim is that we can generate trees with
    a spacing of 2.9m on average. Once extracted, we will update the probability map so we can not have again a tree position there. This will be done
    by  subtracting a normal of 
    """
    
    probs_x = np.sum(probability_map, axis=1)
    probs_y = np.sum(probability_map, axis=0)

    cdf_x = np.cumsum(probs_x)
    cdf_x = cdf_x / np.max(cdf_x)

    cdf_y = np.cumsum(probs_y) 
    cdf_y = cdf_y / np.max(cdf_y)

    ptx = get_position(cdf_x)
    pty = get_position(cdf_y)

    map_update = obtain_normal_update([pty, ptx], [[var / 3, 0.0], [0.0, var / 3]], probability_map.shape)
    map_update = map_update * (1 / map_update.max())

    probability_map = np.clip(probability_map - map_update, 0, None) #We clip values so they are all positive

    return ptx, pty


parser = argparse.ArgumentParser(description='Digiforest Simulator command line arguments')
parser.add_argument('--num_trees', type=int, default=4, help='Number of trees to load into our terrain')
parser.add_argument("--tree_model_path", type=str, default=os.path.join(os.environ["HOME"],
                                            "digiforest_ws/src/digiforest_simulation/resources/models/tree_0"
                                            ), help="Argument to allow the user specify where the tree models are located in his computer")

parser.add_argument('--height_path', type=str, help='Specify a greyscale image to use in the simulator')
parser.add_argument('--terrain_model_path', type=str,
                                    default=os.path.join(os.environ["HOME"],
                                            "digiforest_ws/src/digiforest_simulation/resources/models/digiforest_terrain/materials/textures/heightmap_digiforest.png"
                                            ),
                                    help="Where to store the terrain's model heightmap image")
parser.add_argument("--seed", type=int, default=15,
                     help="Seed number to be used in all of the randome generators. Way to fix our simulations")

args = parser.parse_args()

map_shape = [129, 129, 10]

if args.height_path is None:
    #If there is no heightmap we really want to use, we generate one
    terrain_map_image = generate_heightmap(map_shape[-1])
    io.imsave(args.terrain_model_path, terrain_map_image)
else:
    terrain_map_image = io.imread(args.height_path)


os.system("roscore") #rosmaster needs to be enabled for future sections of the code
temp = subprocess.Popen(["roslaunch", "digiforest_simulation", "spawn_world.launch"]) #Please ensure that spawn_world.launch points to the correct simulation
time.sleep(10)
urdfs = []
x_mult = 1.0
y_mult = 1.0
x_offset = 64.0
y_offset = 64.0
z_offset = 20.0
z_scale = 50.0

random.seed(args.seed)

x_ind = random.randint(0,terrain_map_image.shape[0])
y_ind = random.randint(0,terrain_map_image.shape[1])

z_scale = 10 / terrain_map_image.max()
terrain_map_image *= z_scale


for filename in os.listdir(args.tree_model_path):
	f = os.path.join(args.tree_model_path, filename)
	if os.path.isfile(f) and f.split(".")[-1] == "sdf":
		urdfs.append(f)

package = 'ros_ign_gazebo'
executable = 'create'

launch = roslaunch.scriptapi.ROSLaunch()
launch.start()

xlims = [-50.0, 150.0]
ylims = [-50.0, 50.0]

probabilities = np.ones(terrain_map_image.shape)

for count in range(args.num_trees):
    tree_ind = random.randint(0, len(urdfs)-1)
    model_xml = urdfs[tree_ind]
    print(model_xml)
    pose = Pose()
    pose.orientation.w = 1.0
    model_name = "tree_" + str(count)  # or whatever, just needs to be unique

    x_ind, y_ind = next_position(probabilities)
    x = (x_ind * x_mult - x_offset)
    y = -(y_ind * y_mult - y_offset)
    print(x_ind, y_ind)

    test = terrain_map_image[y_ind, x_ind]
    z = terrain_map_image[y_ind, x_ind]#Value of z must be contained within the terrain we are working with 
    # z = 1.0
    print(z)
    # node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-file " + model_xml + " -urdf -model " + model_name + " -x " + str(x) + " -y " + str(y))
    node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-world heightmap_digiforest_terrain -file " + model_xml + " -name " + model_name + " -x " + str(x) + " -y " + str(y) + " -z " + str(z))
    proc = launch.launch(node)
    time.sleep(0.1)

a = 1
