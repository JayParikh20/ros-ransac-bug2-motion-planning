#!/usr/bin/env python

import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
import numpy as np


def polar2cart(r, theta):
    return r * np.cos(np.deg2rad(theta)), r * np.sin(np.deg2rad(theta))


def odom_data(data: Odometry, args):
    args[1].pose.orientation = data.pose.pose.orientation
    args[2].pose.orientation = data.pose.pose.orientation


def laser_data(data, args):
    # rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.ranges)
    ranges = np.array(data.ranges)
    k = 30
    min_dist = 0.1
    min_points = 20

    # ranges = np.zeros((len(data.ranges), 2))
    # for index in range(len(data.ranges)):
    #     ranges[index] = [data.ranges[index], index / 2]
    # strip_indices = np.where(ranges[:, 0] < 3.0)
    # ranges = ranges[strip_indices]
    #
    # if (ranges.shape[0] > 0):
    #     while (ranges.shape[0] > min_points):
    #         best_inliers_indices = []
    #         iterations = 0
    #         best_inliers_count = 20
    #         best_line = [(0, 0), (0, 0)]
    #         best_line_dist = 0
    #         while (iterations < k):
    #             line_indices = np.random.choice(range(len(ranges)), size=2, replace=False)
    #             x1, y1 = polar2cart(ranges[line_indices[0]][0], ranges[line_indices[0]][1])
    #             x2, y2 = polar2cart(ranges[line_indices[1]][0], ranges[line_indices[1]][1])
    #             inliers_indices = []
    #             for index in range(len(ranges)):
    #                 x0, y0 = polar2cart(ranges[index][0], ranges[index][1])
    #                 distance = abs(((x2 - x1) * (y1 - y0)) - ((x1 - x0) * (y2 - y1))) / np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    #                 if (distance < min_dist):
    #                     inliers_indices.append(index)
    #             line_dist = np.linalg.norm(np.array([x1 - x2, y1 - y2]))
    #             if (len(inliers_indices) >= best_inliers_count and line_dist > best_line_dist):
    #                 best_inliers_indices = inliers_indices
    #                 best_inliers_count = len(inliers_indices)
    #                 best_line = [(x1, y1), (x2, y2)]
    #                 best_line_dist = line_dist
    #             iterations += 1
    #
    #         args[1].points = []
    #         if (len(best_line) >= 2):
    #             args[1].points.append(Point(x=best_line[0][0], y=best_line[0][1], z=0))
    #             args[1].points.append(Point(x=best_line[1][0], y=best_line[1][1], z=0))
    #         if (not rospy.is_shutdown()):
    #             args[0].publish(args[1])
    #
    #         new_ranges = np.delete(ranges, best_inliers_indices, axis=0)
    #         ranges = new_ranges
    iterations = 0
    best_inliers_count = 10
    start_point = (0, 0)
    best_max_dist = 0
    best_line = [(0, 0), (0, 0)]
    point_used = []
    args[2].points = []
    # rospy.loginfo("loop")
    while (iterations < k):
        iterations += 1
        if(len(np.where(ranges < 3.0)[0]) < 1):
            return
        point1, point2 = np.random.choice(np.where(ranges < 3.0)[0], size=2, replace=False)
        x1, y1 = polar2cart(ranges[point1], point1 / 2)
        x2, y2 = polar2cart(ranges[point2], point2 / 2)
        point_used.append(point1)
        point_used.append(point2)
        inliers_indices = []

        for index in range(ranges.shape[0]):
            x0, y0 = polar2cart(ranges[index], index/2)
            distance = abs(((x2 - x1) * (y1 - y0)) - ((x1 - x0) * (y2 - y1))) / np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if (distance < min_dist):
                inliers_indices.append(index)
                if(ranges[index] < 3.0):
                    if(start_point[0] == 0 and start_point[1] == 0):
                        best_line[0] = (x0, y0)
                        start_point = (x0, y0)

                    inlier_dist = np.sqrt((x0 - start_point[0]) ** 2 + (y0 - start_point[1]) ** 2)
                    if (inlier_dist > best_max_dist):
                        best_max_dist = inlier_dist
                        best_line[1] = (x0, y0)

        # args[2].points.append(Point(x=x1, y=y1, z=0))
        # args[2].points.append(Point(x=x2, y=y2, z=0))
        if (len(inliers_indices) >= best_inliers_count):
            # best_inliers_indices = inliers_indices
            best_inliers_count = len(inliers_indices)

    args[1].points = []
    if(best_line):
        args[1].points.append(Point(x=best_line[0][0], y=best_line[0][1], z=0))
        args[1].points.append(Point(x=best_line[1][0], y=best_line[1][1], z=0))
    if (not rospy.is_shutdown()):
        args[0].publish(args[1])

    # Debug scanner
    args[2].points = []
    for index in range(len(data.ranges)):
        xm, ym = polar2cart(data.ranges[index], index / 2)
        args[2].points.append(Point(x=xm, y=ym, z=0))
    if(not rospy.is_shutdown()):
        args[0].publish(args[2])


def init():

    marker_pub = rospy.Publisher("visualization_marker", Marker, queue_size=10)
    line_marker = Marker()
    point_marker = Marker()

    line_marker.header.frame_id = "ransac"
    line_marker.header.stamp = rospy.Time.now()
    line_marker.type = line_marker.LINE_STRIP
    line_marker.id = 0
    line_marker.pose.orientation.w = 1.0
    line_marker.scale.x = 0.1
    line_marker.color.b = 1.0
    line_marker.color.a = 1.0

    point_marker.header.frame_id = "ransac"
    point_marker.header.stamp = rospy.Time.now()
    point_marker.type = line_marker.POINTS
    point_marker.id = 1
    point_marker.scale.x = 0.02
    point_marker.color.r = 1.0
    point_marker.color.a = 1.0

    rospy.Subscriber('/base_scan', LaserScan, laser_data, (marker_pub, line_marker, point_marker))
    # rospy.Subscriber('/odom', Odometry, odom_data, (marker_pub, line_marker, point_marker))

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        rate.sleep()


if __name__ == '__main__':
    rospy.init_node('perception', anonymous=True)
    init()
