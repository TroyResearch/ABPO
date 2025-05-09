# -*- coding: utf-8 -*-

# coding: utf-8
#!/usr/bin/env python
#  Copyright (c). All Rights Reserved.
#  General Optimal control Problem Solver (GOPS)
#  Intelligent Driving Lab (iDLab), Tsinghua University
#
#  Creator: iDLab
#  Lab Leader: Prof. Shengbo Eben Li
#  Email: lisb04@gmail.com
#
#  Description: create offroad_carla env
#  Update Date: 2024-08-25, Fawang Zhang: create environment
import gym
from gops.env.env_gym.recources.waypoints.waypoints import *
import argparse
import glob
import os
import sys
import random
import weakref
from gops.env.env_gym.recources.utills import numpy_imwrite
import torchvision.transforms as transforms
import gops.env.env_gym.recources.const as const
import cv2
import subprocess
import time
import signal
import collections
from gym.utils import seeding


try:
    pwd = os.getcwd()
    search_key = '../../gops/env/env_gym/recources/dist/carla-*%d.*-%s.egg' % (
        sys.version_info.major,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'
    )
    carla_path = glob.glob(search_key)[0]
    sys.path.append(carla_path)

    import carla
    from carla import ColorConverter as cc
except IndexError:
    raise RuntimeError('cannot find carla directory')

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

try:
    import queue
except ImportError:
    import Queue as queue

try:
    import torch
except ImportError:
    raise RuntimeError('cannot import pytorch, make sure pytorch package is installed')

# init position
ENV_INIT_POS = {
    "Offroad_1": [{"pos":(8770.0/100, 5810.0/100, 120.0/100), "yaw":-93.0},
                  {"pos":(-660.0/100, 260.0/100, 120.0/100), "yaw":-195.0}],

    "Offroad_2": [{"pos":(1774.0/100, 4825.0/100, 583.0/100), "yaw":92.0},
                  {"pos":(20417.0/100, 15631.0/100, 411.0/100), "yaw":-55.0}],

    "Offroad_3": [{"pos":(26407.0/100, -4893.0/100, 181.0/100), "yaw":-90.0},
                  {"pos":(-13270.0/100, 3264.0/100, 124.0/100), "yaw":-38.0}],

    "Offroad_4": [{"pos":(-12860.0/100, 22770.0/100, 210.0/100), "yaw":0.0}],

    "Offroad_5": [{"pos":(4738/100, 7365/100, 131/100), "yaw":90},
                  {"pos":(12599/100, 3244/100, 951/100), "yaw":224},
                  {"pos":(6203/100, -12706/100, 214/100), "yaw":69},
                  {"pos":(-9863/100, -13876/100, 388/100), "yaw":162}],

    "Offroad_6": [{"pos":(-12433/100, -11850/100, 99/100), "yaw":126},
                  {"pos":(-2977/100, -11090/100, 548/100), "yaw":66},
                  {"pos":(5308/100, -1616/100, 464/100), "yaw":52},
                  {"pos":(15605/100, 1639/100, 610/100), "yaw":68}],

    "Offroad_7": [{"pos":(-10564/100, -15334/100, 107/100), "yaw":166},
                  {"pos":(-4962/100, 651/100, 276/100), "yaw":134},
                  {"pos":(8814/100, -6371/100, 210/100), "yaw":121},
                  {"pos":(13450/100, 5045/100, 534/100), "yaw":145}],

    "Offroad_8": [{"pos":(-11109/100, 7814/100, 366/100), "yaw":57},
                  {"pos":(4453/100, 14202/100, 300/100), "yaw":-11},
                  {"pos":(11333/100, -14194/100, 483/100), "yaw":45},
                  {"pos":(-4416/100, -4294/100, 158/100), "yaw":210}],

    "Track1": [{"pos":(6187.0/100, 6686.0/100, 138.0/100), "yaw":-91.0}],

    "Town01": [{"pos":(8850.0/100, 9470.0/100, 100.0/100), "yaw":90.0},
               {"pos":(33880.0/100, 24380.0/100, 100.0/100), "yaw":-90.0}],

    "Town02": [{"pos":(8760.0/100, 18760.0/100, 100.0/100), "yaw":-0.0},
               {"pos":(10850.0/100, 30690.0/100, 100.0/100), "yaw":0.0}]
}

ENV_NAME = ENV_INIT_POS.keys()

weatherS = {
    "ClearNoon": carla.WeatherParameters.ClearNoon,
    "CloudyNoon": carla.WeatherParameters.CloudyNoon,
    "WetNoon": carla.WeatherParameters.WetNoon,
    "WetCloudyNoon": carla.WeatherParameters.WetCloudyNoon,
    "MidRainyNoon": carla.WeatherParameters.MidRainyNoon,
    "HardRainNoon": carla.WeatherParameters.HardRainNoon,
    "SoftRainNoon": carla.WeatherParameters.SoftRainNoon,
    "ClearSunset": carla.WeatherParameters.ClearSunset,
    "CloudySunset": carla.WeatherParameters.CloudySunset,
    "WetSunset": carla.WeatherParameters.WetSunset,
    "WetCloudySunset": carla.WeatherParameters.WetCloudySunset,
    "MidRainSunset": carla.WeatherParameters.MidRainSunset,
    "HardRainSunset": carla.WeatherParameters.HardRainSunset,
    "SoftRainSunset": carla.WeatherParameters.SoftRainSunset
}


def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []

def measurement_to_image(state):
    crop_size = (0, 171, 800, 555)
    img = state
    img_ = np.frombuffer(img.raw_data, dtype=np.dtype("uint8"))
    img_ = np.reshape(img_, (img.height, img.width, 4))
    img_ = img_[:, :, :3]
    img_ = img_[:, :, ::-1]
    img_ = img_.astype(np.float32)
    img_ = img_[crop_size[1]:crop_size[3], crop_size[0]: crop_size[2], :]
    img_ /= 255.0

    # img_ = np.resize(img_, (84, 84, 3))
    img_ = np.transpose(img_, (2, 0, 1))
    img_ = np.reshape(img_, (1, img_.shape[0], img_.shape[1], img_.shape[2]))
    return img_


class CarlaOffroadEnv:
    """
    CarlaEnv parameters
        log_dir : save log data path (must write)
        data_dir : data path (Not use)
        host : client host name (default: localhost)
        port : client port number (default: 2000)
        server_path : server`s absolute path (default: CARLA_ROOT)
        server_size : size of server image (default: 400,300)
        image_size : size of client(pygame) image (default: 800,600)
        city_name : name of city name (choose Offroad_1, Offroad_2, Offroad_3, Offroad_4, Track) (default: Offroad_2)
        render : choose render image or not(pygame and server) (default: True)
    """

    city_lenghts = {
        "Offroad_1": 1200,
        "Offroad_2": 670,
        "Offroad_3": 3800,
        "Offroad_4": 7000,
        "Offroad_5": 1800,
        "Offroad_6": 1830,
        "Offroad_7": 2020,
        "Offroad_8": 2390
    }

    def __init__(self,
                 log_dir='./resources/CarlaLog.txt',
                 data_dir=None,
                 host='localhost',
                 port=None,
                 server_path=None,
                 server_size=(400, 300),
                 image_size=(800, 600),
                 fps=10,
                 city_name='Offroad_6',
                 weather='ClearNoon',
                 render=False,
                 render_gcam=False,
                 gcam_target_layer="conv_layer.1.res2",
                 gcam_target_model="IL",
                 plot=False,
                 is_image_state=True):

        self.frame = None
        self.log_dir = log_dir
        self.data_dir = data_dir
        self.delta_seconds = 1.0 / fps
        self.fps = fps
        self.host = host
        self.port = port
        self.server_size = server_size
        self.image_size = image_size
        self.city_name = city_name
        self._render = render
        self.gamma_correction = 2.2
        self.speed_up_steps = 10
        self.timeout_step = 100000
        self._server_path = str(server_path)
        self.is_image_state = is_image_state
        self._settings = None
        self._queues = []
        self._history = []
        self.server = None
        self.server_pid = -99999
        self.client = None  # make client
        self.world = None  # connect client world
        self.setup_client_and_server()
        self.waypoints_manager = get_waypoints_manager(city_name)
        self.world.set_weather(weatherS[weather])
        self.weather = weather

        self.bp = self.world.get_blueprint_library()  # blueprint library

        self.vehicle = None
        self._control = None
        self.sensors = []  # 이미지 센서
        self.collision_sensor = None

        self.set_position()

        self._plot = plot
        if plot:
            self.plotter = Animator(lims=[
                self.waypoints_manager.total_min - 10,
                self.waypoints_manager.total_max + 10
            ])

        self._render_gcam = render_gcam
        # for rendering
        if self._render:
            self.display = None
            self.clock = None
            self.init_for_render()

            if self._render_gcam:
                from main_grad_cam import Gcam_generator
                self.gcam_generator = Gcam_generator(gcam_target_layer, gcam_target_model, cuda=True)

        self._record = False

    def __enter__(self):
        self._settings = self.world.get_settings()
        self.frame = self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False,
            synchronous_mode=True,
            fixed_delta_seconds=self.delta_seconds))

        def make_queue(register_event):
            q = queue.Queue()
            register_event(q.put)
            self._queues.append(q)

        make_queue(self.world.on_tick)

        for sensor in self.sensors:
            make_queue(sensor.listen)

        weak_self = weakref.ref(self)
        self.collision_sensor.listen(lambda event: CarlaOffroadEnv._on_collision(weak_self, event))
        return self

    def __exit__(self, *args, **kwargs):
        self.world.apply_settings(self._settings)

    def _open_server(self):
        with open(self.log_dir, "wb") as out:
            cmd = [os.path.join(os.environ.get('CARLA_ROOT'), 'CarlaUE4.sh'),
                   self.city_name, "-carla-server", "-fps=10", "-world-port={}".format(self.port),
                   "-windwed -ResX={} -ResY={}".format(self.server_size[0], self.server_size[1])
                   ]

            p = subprocess.Popen(cmd, stdout=out, stderr=out)
            time.sleep(5)
        return p

    def _close_server(self):
        no_of_attemps = 0
        try:
            while self.is_process_alive(self.server_pid):
                print("Trying to close Carla server with pid %d" % self.server_pid)
                if no_of_attemps < 5:
                    self.server.terminate()
                elif no_of_attemps < 10:
                    self.server.kill()
                else:
                    os.kill(self.server_pid, signal.SIGKILL)
                time.sleep(1)
                no_of_attemps += 1
        except Exception as e:
            print(e)

    def is_process_alive(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def set_position(self):
        pos, paths = self.waypoints_manager.get_init_pos()
        self.init_paths = paths
        # {pos:[x, y, z], yaw:[yaw]}
        self.init_pos = {
            "pos": (pos[0], pos[1], pos[2] + 2),
            "yaw": pos[3]
        }

        self.init_state = carla.Transform(carla.Location(*self.init_pos["pos"]),
                                          carla.Rotation(yaw=self.init_pos["yaw"]))

    def setup_client_and_server(self):
        # self.server = self._open_server()
        # self.server_pid = self.server.pid
        self.client = carla.Client(self.host, self.port)
        # self.client.read_data()
        self.client.set_timeout(10.0)
        # 원하는 맵을 불러옴
        self.world = self.client.load_world(self.city_name)

    def setup_traffic(self):
        # 获取蓝图库
        blueprint_library = self.world.get_blueprint_library()
        # 定义一些手动路径点
        waypoints = [
            carla.Location(x=118.51087, y=-123.26398, z=9.85117),
            carla.Location(x=-10.60538, y=72.23065, z=2.99218),
            carla.Location(x=11657.255, y=-12620.996, z=844.265),
            carla.Location(x=6585.574, y=-13760.93, z=1384.775)
        ]
        # # 生成车辆
        vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
        spawn_points = carla.Transform(waypoints[0], carla.Rotation(-117.71713295912546))
        vehicle = self.world.spawn_actor(vehicle_bp, spawn_points)

        # 生成行人
        walker_bp = random.choice(blueprint_library.filter('walker.*'))
        walker_spawn_point = carla.Transform(waypoints[1], carla.Rotation(-26.04867607048983))
        walker = self.world.spawn_actor(walker_bp, walker_spawn_point)

        def move_along_path(actor, waypoints, speed=5.0):
            # for target in waypoints:
            #     print(actor.get_location().distance(target))
            #     while actor.get_location().distance(target) > 1.0:
            target = waypoints[3]
            direction = target - actor.get_location()
            # direction = direction.make_unit_vector()
            control = carla.VehicleControl() if isinstance(actor, carla.Vehicle) else carla.WalkerControl()
            if isinstance(actor, carla.Vehicle):
                control.throttle = speed / 10.0
                control.steer = math.atan2(direction.y, direction.x) / math.pi
            else:
                control.direction = direction
                control.speed = speed
            actor.apply_control(control)
            time.sleep(1)

        # # 移动车辆和行人

        vehicle_mover = move_along_path(vehicle, waypoints)
        move_along_path(walker, waypoints, speed=2.0)

        try:
            while True:
                self.world.tick()
                next(vehicle_mover)
                self.display.fill((0, 0, 0))
                pygame.display.flip()

        finally:
            # 清理
            vehicle.destroy()
            walker.destroy()

    def step(self, action, timeout=2.0):
        # observation
        measurement, sensor_data = self.tick(timeout)

        # apply action to environment
        if type(action) == torch.Tensor:
            action = action.squeeze(0).detach().numpy().tolist()
        elif type(action) == np.ndarray:
            action = action.tolist()
        if len(action) == 2:
            self._control.steer = action[1]
            self._control.throttle = action[0]
        elif len(action) == 3:
            self._control.brake = action[2]
            self._control.steer = action[1]
            self._control.throttle = action[0]
        elif len(action) == 1:
            self._control.steer = action[0]
            self._control.throttle = 0.5
            self._control.brake = 0
        else:
            raise ValueError("Not match action size")

        if self._control.throttle < 0:
            self._control.reverse = True
        else:
            self._control.reverse = False

        self.vehicle.apply_control(self._control)

        self.update_epinfos(measurement)
        self.epinfos["action"] = action
        reward, done = self.get_reward_done(self.epinfos)
        self.observation = (measurement, sensor_data)

        return self.preprocess_observation(self.observation), reward, done, self.epinfos

    def reset_epinfos(self):
        self.epinfos = {
            "location": np.array(self.init_pos["pos"][0:3]),
            "out_count": 0,
            "nospeedtime_step": 0,
            "current_step": 0,
            "goal_waypoint_idx": 0,
            "distance_from_goal_waypoint": -1,
            "yaw_error2goal_waypoint":0,
            "progress": 0,
            "track_width": 3,
            "speed": 0,
            "passed_wps": [],
            "paths": self.init_paths,
            "mileage": 0,
            "distance_from_center": 0,
            "cumulative_speed": 0,
            "label_steers":[]
        }

    def reset(self, timeout=2.0, reset_position=True):
        # close all actor in environment
        self._close()
        # set self-vehicle x y z & yaw
        if reset_position:
            self.set_position()
        self.reset_epinfos()
        # set initial setting
        if self.vehicle is None:
            self._build_vehicle()
        if isinstance(self.vehicle, carla.Vehicle):
            self._control = carla.VehicleControl()
        else:
            self._control = None
        # Three cameras, one rgb, one depth and one for visulization
        if len(self.sensors) == 0:
            self._build_sensors()

        if len(self._queues) != 0:
            del self._queues[:]

        self._history = []

        self.__enter__()

        time.sleep(1)
        # for skip initial few steps
        for i in range(self.speed_up_steps):
            self.tick(1)

            _control = carla.VehicleControl()
            _control.steer = 0
            _control.throttle = 10
            _control.brake = 0
            _control.hand_brake = False
            _control.reverse = False
            time.sleep(0.05)
            self.vehicle.apply_control(_control)

        self.observation = self.tick(timeout)
        self.update_epinfos(self.observation[0])
        return self.preprocess_observation(self.observation), self.epinfos

    def update_epinfos(self, measurement):
        t = measurement['transform']
        v = measurement['velocity']

        speed = math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
        location = np.array([t.location.x, t.location.y]) #, t.location.z
        car_heading = t.rotation.yaw/180*3.14
        # todo add road elevation
        collision = measurement['collision']

        # update goal_waypoint_idx
        current_wp_index = self.waypoints_manager.get_current_wp_index(location)

        current_wp = np.array(self.waypoints_manager.get_wp(current_wp_index))

        current_wp_distance = np.sum(
            ((np.array(location) - current_wp) ** 2))
        current_wp_distance = current_wp_distance ** 0.5
        current_wp_yaw_error = 0
        global_path_len = 10
        self.global_path = self.waypoints_manager.get_global_wp(current_wp_index, global_path_len)

        if len(self.epinfos["passed_wps"]) > 0:
            if self.epinfos["passed_wps"][-1] != current_wp_index and current_wp_distance < 5:
                # paths = self.waypoints_manager.get_paths(location, current_wp_index, self.epinfos["passed_wps"][-1])
                self.epinfos["passed_wps"].append(current_wp_index)
            else:
                pass
        else:
            self.epinfos["passed_wps"].append(current_wp_index)

            # paths = self.epinfos["paths"]
        # ?
        paths = self.waypoints_manager.get_paths(location, current_wp_index, self.epinfos["passed_wps"][-1])

        # mileage
        mileage = self.waypoints_manager.get_mileage(self.epinfos["passed_wps"])

        # track width  ?
        track_width = self.waypoints_manager.get_track_width(current_wp_index)

        # nospeedtime_step
        nospeedtime_step = self.epinfos["nospeedtime_step"]
        if speed * 3.6 <= 1.0:
            nospeedtime_step += 1

        # current_step
        current_step = self.epinfos["current_step"] + 1

        epinfos = {}
        epinfos["speed"] = speed
        epinfos["prev_speed"] = self.epinfos["speed"]
        epinfos["location"] = location
        epinfos["prev_location"] = self.epinfos["location"]
        epinfos["passed_wps"] = self.epinfos["passed_wps"]
        epinfos["current_step"] = current_step
        epinfos["mileage"] = mileage
        epinfos["prev_mileage"] = self.epinfos["mileage"]
        epinfos["track_width"] = track_width + 4
        epinfos["is_collision"] = True if collision > 0 else False
        epinfos["nospeedtime_step"] = nospeedtime_step
        epinfos["current_heading"] = car_heading
        epinfos["paths"] = paths
        epinfos["current_wp_index"] = current_wp_index
        epinfos["prev_paths"] = self.epinfos["paths"]
        # epinfos["distance_from_center"] = sum([path["distance_from_center"] for path in paths])/len(paths)
        epinfos["distance_from_center"] = current_wp_distance
        epinfos["yaw_error2goal_waypoint"] = current_wp_yaw_error
        epinfos["cumulative_speed"] = self.epinfos["cumulative_speed"] + speed
        epinfos["average_speed"] = epinfos["cumulative_speed"] / current_step

        if self._plot:

            all_prev_wps = []
            all_next_wps = []
            for path in paths:
                all_prev_wps += path["prev_wps"].tolist()
                all_next_wps += path["next_wps"].tolist()

            all_prev_wps = np.asarray(all_prev_wps)
            all_next_wps = np.asarray(all_next_wps)

            points_group = {}

            if epinfos["current_step"] == 1:
                points_group['waypoints'] = [np.asarray(self.waypoints_manager.get_all_wps()), 3]

            points_group['previous waypoints'] = [all_prev_wps, 5]
            points_group['next waypoints'] = [all_next_wps, 5]
            points_group['location'] = [np.asarray([location]), 10]
            points_group['init pos'] = [np.asarray([self.init_pos["pos"][0:2]]), 10]

            self.plotter.plot_points(points_group)

            radian = car_heading
            way_vector = np.array([math.cos(radian), math.sin(radian)])
            car_slope = get_slope(location, location + way_vector)
            car_bias = get_bias(car_slope, location)

            linear_group = {
                'car heading': [car_slope, car_bias, int(location[0]) - 3, int(location[0]) + 3]
            }

            for path in paths:
                linear_group['wp heading'] = [
                    path["heading_slope"],
                    path["heading_bias"],
                    int(location[0]) - 3,
                    int(location[0]) + 3
                ]

            self.plotter.plot_linears(linear_group)
            self.plotter.update()

        self.epinfos = epinfos

    def get_reward_done(self, epinfos):
        distance = max([epinfos["paths"][i]["distance_from_next_waypoints"][0] for i in range(len(epinfos["paths"]))])
        prev_distance = max(
            [epinfos["prev_paths"][i]["distance_from_next_waypoints"][0] for i in range(len(epinfos["prev_paths"]))])

        waypoints_heading = self.epinfos["paths"][0]["heading"]
        current_heading = self.epinfos["current_heading"]
        speed = self.epinfos["speed"]
        current_wp_index = epinfos["current_wp_index"]
        distance_from_center = epinfos["distance_from_center"]
        progress = self.epinfos["mileage"] / 100
        prev_progress = self.epinfos["prev_mileage"] / 100

        reward = 0
        done = False

        max_reward = 1
        min_reward = -1

        if prev_distance > 0:
            if distance > prev_distance and epinfos["current_wp_index"] == epinfos["passed_wps"][-1]:
                distance_reward = 0
            else:
                distance_reward = (prev_distance - distance)
            speed_reward = 0.05 * speed
            center_reward = -0.1 * distance_from_center
            heading_reward = -(abs(waypoints_heading - current_heading) / 180 * 3.14)
            reward = distance_reward + center_reward + heading_reward + speed_reward
        # reward = min(max(reward, min_reward), max_reward)

        '''
        if prev_distance > 0:
            if distance > prev_distance and epinfos["current_wp_index"] == epinfos["passed_wps"][-1]:
                reward = 0
            else:
                if abs(distance - prev_distance) < 0.1:
                    reward = 0
                else:
                    if abs(waypoints_heading - current_heading) < 15:
                        reward = 2
                    else:
                        reward = 1

        progress_diff = progress / self.epinfos["current_step"]
        progress_diff *= 1000
        reward += progress_diff
        reward -= distance_from_center

        if prev_distance > 0:
            if distance > prev_distance and epinfos["goal_waypoint_idx"] == epinfos["prev_goal_waypoint_idx"]:
                reward = 0
            else:
                if abs(distance - prev_distance) > 0:
                    reward += 1
                else:
                    reward -= 1
        '''

        if epinfos["nospeedtime_step"] > 20 and epinfos["current_step"] > 40:
            done = True

        if self.waypoints_manager.city_num > 4:
            if self.waypoints_manager.raw_waypoints.iloc[current_wp_index]["inter_id"] != -1:
                epinfos["track_width"] += 3

        # if epinfos["distance_from_center"] > epinfos["track_width"] / 2:
        #     done = True

        if epinfos['is_collision']:
            done = True

        if done:
            reward = -1000

        return -reward, done

    def get_sensor_observation(self):
        # path_idx = random.randint(0, len(self.epinfos["paths"])-1)
        path_idx = 0

        speed = self.epinfos["speed"]
        location = self.epinfos["location"]

        next_wps = self.epinfos["paths"][path_idx]["next_wps"]
        waypoints_heading = self.epinfos["paths"][path_idx]["heading"]

        current_heading = self.epinfos["current_heading"]
        distance_from_center = self.epinfos["paths"][path_idx]["distance_from_center"]
        track_width = self.epinfos["track_width"]
        current_way_vector = get_vector_from_degree(current_heading)

        label_steers = []
        for nwp in next_wps:
            way_vector = nwp - location
            way_vector = way_vector / ((way_vector[0] ** 2 + way_vector[1] ** 2) ** 0.5)
            new_way_vector = linear_transform(current_way_vector, way_vector)
            label_steers.append(new_way_vector[1])

        result = [
            speed / 4,
            label_steers,
            abs(abs(waypoints_heading) - abs(current_heading)) / 180,
            # (waypoints_heading - current_heading) / 180*np.pi,
            distance_from_center / 2,
            track_width / 2
        ]

        result = np.array(result)
        return result

    def preprocess_observation(self, observation):
        '''
        rgb_image = observation[1]['rgb']
        save_img = np.array(measurement_to_image(rgb_image)[0])
        numpy_imwrite(save_img, "{}_{}_{}.png".format(self.city_name, self.weather, 4))
        '''

        if self.is_image_state:
            rgb_image = observation[1]['rgb']
            depth_image = observation[1]["depth"]
            result = np.array(measurement_to_image(rgb_image)[0])
        else:
            result = self.get_sensor_observation()
        return result

    def get_full_observation(self):
        rgb_image = np.array(measurement_to_image(self.observation[1]['rgb'])[0])
        depth_image = np.array(measurement_to_image(self.observation[1]['depth'])[0])
        sensors = self.get_sensor_observation()
        return rgb_image, depth_image, sensors

    def init_for_render(self):
        pygame.init()
        self.display = pygame.display.set_mode((self.image_size[0], self.image_size[1]),
                                               pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

    def start_record(self, video_name):
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.video_writer = cv2.VideoWriter(video_name, fourcc, 15, self.image_size)
        self._record = True

    def save_record(self):
        self.video_writer.release()

    def render(self, image_type='visual', blend=False, save=False, model=None, step=0):
        if self._render_gcam:
            image_type = 'rgb'

        if self._render:
            self.clock.tick()
            image = self.observation[1][image_type]
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]

            if self._render_gcam:
                array = self.gcam_generator(array, self.epinfos["speed"])

            if self._record:
                self.video_writer.write(array)

            image_surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

            if save:
                zero = (5 - len(str(step))) * '0'
                if not os.path.exists('./videos/{}'.format(model)):
                    os.mkdir('./videos/{}'.format(model))
                pygame.image.save(image_surface, './videos/{}/image_{}{}.jpg'.format(model, zero, step))
            if blend:
                image_surface.set_alpha(100)
            self.display.blit(image_surface, (0, 0))
            pygame.display.flip()
        else:
            pass

    def get_verbose(self):
        verbose = {}
        verbose_keys = [
            "speed",
            "mileage",
            "distance_from_center",
            "track_width",
            "current_step"
        ]
        for key in verbose_keys:
            verbose[key] = self.epinfos[key]
        return verbose

    # get state at every step
    def tick(self, timeout):
        self.frame = self.world.tick()

        data = []
        for i, q in enumerate(self._queues):
            data.append(self._retrieve_data(q, timeout))

        assert all(x.frame == self.frame for x in data)
        snapshot = data[0].find(self.vehicle.id)
        # [pos, vel, angular_vel, accel, collision]
        _measurement = self.get_measurements(snapshot)
        # img{rgb, depth, visual}
        sensor_data = self.get_images(data[1:])
        return _measurement, sensor_data

    def _retrieve_data(self, sensor_queue, timeout):
        while True:
            while True:
                try:
                    data = sensor_queue.get(timeout=timeout)
                    break
                except queue.Empty:
                    print('Queue Empty')
                    time.sleep(1)

            if data.frame == self.frame:
                return data
        '''
        while True:
            try:
                data = sensor_queue.get(timeout=timeout)
            except queue.Empty:
                pass

            if data.frame == self.frame:
                return data
        '''

    def _build_vehicle(self):
        blueprint = self.bp.filter('vehicle.nissan.patrol')[0]
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'true')

        while True:
            try:
                self.vehicle = self.world.spawn_actor(
                    blueprint,  # fixed vehicle
                    self.init_state
                )  # ego vehicle
                break
            except:
                print("RuntimeError: Spawn failed because of collision at spawn position")
                print("Respawn")
                pos = list(self.init_pos["pos"])
                pos[-1] += 5
                self.init_pos["pos"] = tuple(pos)
                self.init_state = carla.Transform(carla.Location(*self.init_pos["pos"]),
                                                  carla.Rotation(yaw=self.init_pos["yaw"]))

    def _build_sensors(self):
        sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)'],
            ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)'],
            ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)'],
            ['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
             'Camera Semantic Segmentation (CityScapes Palette)'],
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]

        camera_transform = carla.Transform(carla.Location(x=2.0, z=1.7), carla.Rotation())
        # for visualize
        render_camera_transform = carla.Transform(carla.Location(x=-8, z=6), carla.Rotation(pitch=8.0))

        for item in sensors:
            bp = self.bp.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(self.image_size[0]))
                bp.set_attribute('image_size_y', str(self.image_size[1]))
            if bp.has_attribute('gamma'):
                bp.set_attribute('gamma', str(self.gamma_correction))
            elif item[0].startswith('sensor.lidar'):
                bp.set_attribute('range', '5000')
                item.append(bp)

        camera_rgb = self.world.spawn_actor(
            self.bp.find(sensors[0][0]),
            camera_transform,
            attach_to=self.vehicle, attachment_type=carla.AttachmentType.Rigid)
        camera_depth = self.world.spawn_actor(
            self.bp.find(sensors[2][0]),
            camera_transform,
            attach_to=self.vehicle, attachment_type=carla.AttachmentType.Rigid)
        visual_camera = self.world.spawn_actor(
            self.bp.find(sensors[0][0]),
            render_camera_transform,
            attach_to=self.vehicle, attachment_type=carla.AttachmentType.SpringArm)

        self.collision_sensor = self.world.spawn_actor(
            self.bp.find('sensor.other.collision'),
            carla.Transform(),
            attach_to=self.vehicle)

        self.sensors.append(camera_rgb)
        self.sensors.append(camera_depth)
        self.sensors.append(visual_camera)

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self._history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self._history.append((event.frame, intensity))
        if len(self._history) > 4000:
            self._history.pop(0)

    def get_measurements(self, snapshot):
        collision_history = self.get_collision_history()

        if self.frame in collision_history.keys():
            return {'transform': snapshot.get_transform(), 'velocity': snapshot.get_velocity(),
                    'angular_velocity': snapshot.get_angular_velocity(), 'acceleration': snapshot.get_acceleration(),
                    'collision': collision_history[self.frame]}
        else:
            return {'transform': snapshot.get_transform(), 'velocity': snapshot.get_velocity(),
                    'angular_velocity': snapshot.get_angular_velocity(), 'acceleration': snapshot.get_acceleration(),
                    'collision': 0}

    def get_images(self, data):
        data[1].convert(cc.LogarithmicDepth)
        return {'rgb': data[0], 'depth': data[1], 'visual': data[2]}

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return seed

    def _close(self):
        for sensor in self.sensors:
            if sensor is not None:
                sensor.destroy()

        if self.collision_sensor is not None:
            self.collision_sensor.destroy()

        if self.vehicle is not None:
            self.vehicle.destroy()

        self.sensors = []
        self.collision_sensor = None
        self.vehicle = None

    def close(self):
        self._close()
        # self._close_server()
        pygame.quit()


class Env(CarlaOffroadEnv):
    """
    Environment wrapper for CarRacing
    """

    def __init__(self, **kwargs):

        self.env = CarlaOffroadEnv(
        render=kwargs['is_render'],
        render_gcam=False,
        plot=False,
        port=kwargs['port'],
        server_size=(4, 3),
        city_name='Offroad_1', #kwargs['city_name']
        weather='ClearNoon', #kwargs['weather'],
        is_image_state=True)
        n_traj_points = 10
        self.action_space = gym.spaces.Box(
            low=-0.1, high=0.1, shape=(n_traj_points*2, ), dtype=np.float64
        )

        feature_size = 921600+5
        self.observation_space = gym.spaces.Box(
            low=np.array([-np.inf] * feature_size),
            high=np.array([np.inf] * feature_size),
            dtype=np.float32,
        )

        self.planned_traj = np.zeros_like((10, 2))

    def reset(self):
        img, info = self.env.reset()
        label_steers = self.env.get_sensor_observation()[1]
        info["label_steers"] = label_steers
        yaw_error2goal_waypoint = self.env.get_sensor_observation()[2]
        info["yaw_error2goal_waypoint"] = yaw_error2goal_waypoint
        img = img.reshape((1, -1))
        obs_array_norm = np.array([info["location"][0]/100, info["location"][1]/100, info["speed"]/20, info['distance_from_center']/100, info["yaw_error2goal_waypoint"]/10]).reshape((1, -1))
        state = np.concatenate((img, obs_array_norm), 1)
        return state, info

    def step(self, action):
        img, reward, done, info = self.env.step(action[:2])
        img = img.reshape((1, -1))
        yaw_error2goal_waypoint = self.env.get_sensor_observation()[2]
        info["yaw_error2goal_waypoint"] = yaw_error2goal_waypoint
        obs_array_norm = np.array([info["location"][0]/100, info["location"][1]/100,info["speed"] / 20, info['distance_from_center'] / 100, info["yaw_error2goal_waypoint"] / 10]).reshape(
            (1, -1))
        state = np.concatenate((img, obs_array_norm), 1)
        dist2global_reward = self.get_reward()
        reward = reward + dist2global_reward
        return state, reward, done, info

    def get_reward(self):
        dist2global_reward = np.sum(np.sqrt(np.sum((self.env.global_path - self.planned_traj) ** 2, axis=1)))

        return -dist2global_reward

    def update_loca_traj(self, local_traj):
        self.planned_traj = local_traj

    def get_global_path(self):
        return self.env.global_path

    def seed(self, seed=None):
        self.env.seed(seed)

    def render(self, step):
        self.env.render(step=step)

    def close(self):
        self.env.close()


def env_creator(**kwargs):
    """
    make env `gym_offroadcarla‘
    """

    return Env(**kwargs)






if __name__ == '__main__':
    # Parameters Setup
    parser = argparse.ArgumentParser()
    parser.add_argument('--city-name', default='Offroad_8', type=str)
    parser.add_argument('--weather', default='ClearNoon', type=str)
    parser.add_argument('--max-episode', default=1, type=int)
    parser.add_argument('--max-step', default=3000, type=int)
    parser.add_argument('--is_render', default=True, type=bool, help='render pygame')
    parser.add_argument('--plot', default=False, type=bool)
    args = vars(parser.parse_args())

    env = env_creator(**args)

    from gops.utils.control.rule_based_controller import mathDriver

    agent = mathDriver(speed_limits=[5, 6])
    print(env.observation_space)
    print(env.action_space)
    print(env.action_space.sample())

    total_step = 0
    total_reward = 0
    try:
        for episode in range(args['max_episode']):
            state, info = env.reset()
            episode_reward = 0
            step = 0
            done = False
            while not done:
                print("step:", step)
                step += 1

                if args['is_render']:
                    if episode % 100 == 0:
                        env.render(step=step)
                    else:
                        env.render()
                state2controller = [info["speed"], info["label_steers"],info["yaw_error2goal_waypoint"], info["distance_from_center"]/2,info["track_width"]/2 ]
                action = agent.get_action(state2controller)
                next_state, reward, done, _ = env.step(action)

                next_obs = next_state
                total_step += 1
                episode_reward += reward
                state = next_state


                if total_step > args['max_step']:
                    break

            total_reward += episode_reward
            print("#{}-th Episode, Total_Reward {}".format(episode, episode_reward))

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        env.close()




