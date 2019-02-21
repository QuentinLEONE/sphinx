import paramiko
import scp
import os
import json
import time
from datetime import datetime

from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2 as cv


def ssh_connection(conf):
	print("SSH connection")
	ssh_client = paramiko.SSHClient()
	ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh_client.connect(hostname=conf["hostname"], username=conf["username"], password=conf["password"])
	print("\t... connected")
	return ssh_client


def get_current_time():
	return str(datetime.now()).replace(" ", "T")
 

def find_faces(img):
	face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')
	gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
	faces = face_cascade.detectMultiScale(gray, 1.3, 2)
	return faces


def camera_initialisation():
	print("initialise camera")
	camera = PiCamera()
	camera.resolution = (640, 480)
	camera.framerate = 32
	rawCapture = PiRGBArray(camera, size=(640, 480))
	print("\t...initialised")
	time.sleep(0.1)
	return camera, rawCapture


def save_faces(faces, folder):
	for (x, y, w, h) in faces:
		face = image[y:y+h, x:x+w]
		cv.imwrite(folder + get_current_time() + ".jpg", face)


def scp_faces(faces, scp_client, remote_path):
	for (x, y, w, h) in faces:
		face = image[y:y+h, x:x+w]
		filename_tmp = get_current_time() + ".jpg"
		cv.imwrite(filename_tmp, face)
		scp_client.put(filename_tmp, remote_path)
		os.system("rm " + filename_tmp)
 

if __name__ == "__main__":
	with open("conf.json", "r") as f:
		conf = json.load(f)
	ssh_client = ssh_connection(conf["scp"])
	scp_client = scp.SCPClient(ssh_client.get_transport())
	camera, rawCapture = camera_initialisation()
	print("Sphinx is ready")
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		image = frame.array
		faces = find_faces(image)
		if len(faces) > 0:
			print("Faces detected!")
			scp_faces(faces, scp_client, conf["scp"]["remote_path"])
		rawCapture.truncate(0)
	ftp_client.close()
	ssh_client.close()
