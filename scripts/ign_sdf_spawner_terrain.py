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

# model_xml = rospy.get_param("/foo/robot_description")

# model_dir = "/home/mihir/Documents/Research/digiforest/3d_models/generator/procedural_urdf_tree_generator/tree_models"
# model_dir = "/home/mihir/Documents/Research/digiforest/3d_models/generator/procedural_urdf_tree_generator/tree_models/sdfs"
model_dir = "/home/mihir/Documents/Research/digiforest/3d_models/generator/procedural_urdf_tree_generator/tree_models/real_trees/ign"
urdfs = []

terrain_map_image_path = "/home/mihir/.ignition/fuel/fuel.ignitionrobotics.org/chapulina/models/heightmap bowl/1/materials/textures/heightmap_bowl.png"
terrain_map_image = io.imread(terrain_map_image_path)
x_mult = 1.0
y_mult = 1.0
x_offset = 64.0
y_offset = 64.0
z_offset = 20.0
z_scale = 50.0

random.seed(time.time())

x_ind = random.randint(0,terrain_map_image.shape[0])
y_ind = random.randint(0,terrain_map_image.shape[1])
# print(x_ind, y_ind)

for filename in os.listdir(model_dir):
	f = os.path.join(model_dir, filename)
	if os.path.isfile(f):
		urdfs.append(f)
package = 'ros_ign_gazebo'
executable = 'create'

launch = roslaunch.scriptapi.ROSLaunch()
launch.start()

xlims = [-50.0, 150.0]
ylims = [-50.0, 50.0]

num_trees = 4
for count in range(0,num_trees):
	tree_ind = random.randint(0, len(urdfs)-1)
	model_xml = urdfs[tree_ind]
	print(model_xml)
	pose = Pose()
	pose.orientation.w = 1.0
	model_name = "tree_" + str(count+30)  # or whatever, just needs to be unique
	# x = random.uniform(xlims[0], xlims[1])
	# y = random.uniform(ylims[0], ylims[1])
	x_ind = random.randint(0,terrain_map_image.shape[0]-1)
	y_ind = random.randint(0,terrain_map_image.shape[1]-1)
	x = (x_ind * x_mult - x_offset)
	y = -(y_ind * y_mult - y_offset)
	print(x_ind, y_ind)
	z = z_scale*(terrain_map_image[y_ind, x_ind][0]/255.0) - z_offset
	# z = 1.0
	print(z)
	# node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-file " + model_xml + " -urdf -model " + model_name + " -x " + str(x) + " -y " + str(y))
	node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-world heightmap -file " + model_xml + " -name " + model_name + " -x " + str(x) + " -y " + str(y) + " -z " + str(z))
	proc = launch.launch(node)
	time.sleep(0.1)
