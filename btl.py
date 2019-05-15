import math
import matplotlib
import matplotlib.pyplot as plt
import keyboard
from ai2thor.controller import Controller
import copy
import numpy as np
from PIL import Image, ImageDraw

matplotlib.use("TkAgg", warn=False)

# Class change agent's 3D position to 2D
class ThorPositionTo2DFrameTranslator(object):
    def __init__(self, frame_shape, cam_position, orth_size):
        self.frame_shape = frame_shape
        self.lower_left = np.array((cam_position[0], cam_position[2])) - orth_size
        self.span = 2 * orth_size

    def __call__(self, position):
        if len(position) == 3:
            x, _, z = position
        else:
            x, z = position
	
        camera_position = (np.array((x, z)) - self.lower_left) / self.span
        return np.array(
            (
                round(self.frame_shape[0] * (1.0 - camera_position[1])),
                round(self.frame_shape[1] * camera_position[0]),
            ),
	    dtype = int,
        

def position_to_tuple(position):
    return (position["x"], position["y"], position["z"])

# Function that get agent infomations
def get_agent_map_data(c):
    c.step({"action": "ToggleMapView"})
    cam_position = c.last_event.metadata["cameraPosition"]
    cam_orth_size = c.last_event.metadata["cameraOrthSize"]
    pos_translator = ThorPositionTo2DFrameTranslator(
        c.last_event.frame.shape, position_to_tuple(cam_position), cam_orth_size
    )
    to_return = {
        "frame": c.last_event.frame,
        "cam_position": cam_position,
        "cam_orth_size": cam_orth_size,
        "pos_translator": pos_translator,
    }
    c.step({"action": "ToggleMapView"})
    return to_return


def add_agent_view_triangle(
    position, rotation, frame, pos_translator, scale=1.0, opacity=0.7
):
    img1 = Image.fromarray(frame.astype("uint8"), "RGB").convert("RGBA")
    img2 = Image.new("RGBA", frame.shape[:-1])
    
    offs = 10
    draw2 = ImageDraw.Draw(img2)
    first = 0
    p_last = tuple(reversed(pos_translator(tracedPos[0])))

    # Draw trajectories	 		
    for p0_ in tracedPos:
	p1 = copy.copy(p0_)
	p2 = copy.copy(p0_)
	cirPoints = []
	flag = 0
    	for p in [p1, p2]:
		px = pos_translator(p)
		if (flag == 0):
			px[0] -=offs
			px[1] -=offs
		else:
			px[0]+=offs
			px[1]+=offs
		cirPoints.append(tuple(reversed(px)))
		flag = 1-flag
	draw2.ellipse(cirPoints,fill=(255,255,0, 255))

	if (first != 0):
		p_now = tuple(reversed(pos_translator(p0_)))
		draw2.line([p_last,p_now], fill=(255,255,0,255), width = 20)
		p_last = p_now
	else:
		first = 1
	
    img = Image.alpha_composite(img1, img2)
    return np.array(img.convert("RGB"))


if __name__ == "__main__":    
    c = Controller()
    c.start()
    c.reset("FloorPlan1_physics")
    event = c.step(dict(action='Initialize', gridSize=0.25, makeAgentsVisible = False))
    tracedPos = []
    tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
    posY = event.metadata['agent']['rotation']['y']	

    # Agent controller		
    while True:
	if keyboard.is_pressed('w'):
		event = c.step(dict(action = 'MoveAhead'))
		tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
	elif keyboard.is_pressed('s'):
		event = c.step(dict(action = 'MoveBack'))
		tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
	elif keyboard.is_pressed('a'):
		posY -= 10
		event = c.step(dict(action = 'Rotate', rotation = posY))  
	elif keyboard.is_pressed('d'):
		posY += 10
		event = c.step(dict(action = 'Rotate', rotation = posY)) 
	elif keyboard.is_pressed('up'):
		event = c.step(dict(action = 'LookUp'))
		tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
	elif keyboard.is_pressed('down'):
		event = c.step(dict(action = 'LookDown'))
	elif keyboard.is_pressed('left'):
		event = c.step(dict(action = 'MoveLeft'))
		tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
	elif keyboard.is_pressed('right'):
		event = c.step(dict(action = 'MoveRight'))
		tracedPos.append(position_to_tuple(c.last_event.metadata["agent"]["position"]))
	elif keyboard.is_pressed('f'):
		t = get_agent_map_data(c)
		new_frame = add_agent_view_triangle(
			position_to_tuple(c.last_event.metadata["agent"]["position"]),
			c.last_event.metadata["agent"]["rotation"]["y"],
			t["frame"],
			t["pos_translator"],
		)
		plt.imshow(new_frame)
		plt.show()
