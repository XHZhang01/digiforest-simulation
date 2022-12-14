
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

random.seed(time.time())

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

num_trees = 500
for count in range(0,num_trees):
	tree_ind = random.randint(0, len(urdfs)-1)
	model_xml = urdfs[tree_ind]
	print(model_xml)
	pose = Pose()
	pose.orientation.w = 1.0
	model_name = "tree_" + str(count+100)  # or whatever, just needs to be unique
	x = random.uniform(xlims[0], xlims[1])
	y = random.uniform(ylims[0], ylims[1])
	# node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-file " + model_xml + " -urdf -model " + model_name + " -x " + str(x) + " -y " + str(y))
	node = roslaunch.core.Node(package=package, node_type=executable, name= "tree_spawner_" + model_name, args="-world empty_world -file " + model_xml + " -name " + model_name + " -x " + str(x) + " -y " + str(y))
	proc = launch.launch(node)
	time.sleep(0.1)
	# proc.stop()
	# # may want to delet the model first
	# # delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)
	# # delete_model(model_name)
	# spawn_model = rospy.ServiceProxy('/gazebo/spawn_urdf_model', SpawnModel)
	# req = SpawnModelRequest()
	# req.model_name = model_name
	# req.model_xml = model_xml
	# # should this be unique so ros_control can use each individually?
	# req.robot_namespace = "/foo"
	# req.initial_pose = pose
	# resp = spawn_model(req)