import math
import matplotlib.pyplot as plt
import requests
import sys
import time


def overpass_query(iso_sub_code, classification):
	"""returns json response of ways where highway=classification in iso_code area"""
	url = "http://overpass-api.de/api/interpreter"
	query = f"""
	[out:json][timeout:5000];
	area["ISO3166-2"="{iso_sub_code}"];
	way[highway={classification.lower()}](area);
	(._;>;);
	out body;
	"""

	response = requests.get(url, params={'data':query})

	try:
		response.raise_for_status()
	except Exception as X:
		print("Request failed: {}.\nWaiting one minute to retry...\n".format(X))
		time.sleep(60)
		response = requests.get(url, params={'data':query})

	return response.json()


"""
Radius and equation from GIS Fundamentals 5th Ed. by Paul Bolstad
"""


def gc_distance(point1, point2):
	"""returns distance between point1 and point2 using great circle equation"""
	lon1, lat1 = point1[0], point1[1]
	lon2, lat2 = point2[0], point2[1]
	lat1, lat2, lon1, lon2 = map(math.radians, [lat1, lat2, lon1, lon2])
	radius = 6378 # WGS84 equatorial radius in km

	trig = math.sin(lat1) * math.sin(lat2) + math.cos(lat1)\
				 * math.cos(lat2) * math.cos(lon1 - lon2)

	if trig >= 1:
		distance = 0
	else:
		distance = radius * math.acos(trig)

	return distance


def class_distance(json_data):
	"""returns total distance and nodes of a given classification"""
	total_distance = 0
	node_coords = {}
	nodes = 0

	for feature in json_data["elements"]:
		if feature["type"] == "node":
			node_coords[str(feature["id"])] = (feature["lon"], feature["lat"])
			nodes += 1
		elif feature["type"] == "way":
			coords = []
			way_distance = 0
			for node_id in feature["nodes"]:
				coord = node_coords[str(node_id)]
				coords.insert(0, coord)
				if len(coords) < 2:
					continue
				else:
					p1 = coords[0]
					p2 = coords[1]
					way_distance += gc_distance(p1, p2)
					coords.pop()

			total_distance += way_distance

	return (total_distance, nodes)


def class_piechart(class_dict, fignum=1):
	"""plots a piechart of classification proportions"""
	labels, sizes = class_dict.keys(), class_dict.values()
	fig = plt.figure(fignum)
	ax = fig.add_axes([0, 0, 1, 1])
	ax.axis('equal')
	ax.pie(sizes, labels = labels, autopct='%1.2f%%')

	return fig


def main():
	d_proportions = {}
	sys_iso_area = sys.argv
	
	motorway = class_distance(overpass_query(sys_iso_area[1], "motorway"))
	trunk = class_distance(overpass_query(sys_iso_area[1], "trunk"))
	primary = class_distance(overpass_query(sys_iso_area[1], "primary"))
	secondary = class_distance(overpass_query(sys_iso_area[1], "secondary"))
	tertiary = class_distance(overpass_query(sys_iso_area[1], "tertiary"))
	unclassified = class_distance(overpass_query(sys_iso_area[1], "unclassified"))
	residential = class_distance(overpass_query(sys_iso_area[1], "residential"))
	service = class_distance(overpass_query(sys_iso_area[1], "service"))

	d_proportions["motorway"] = motorway[0]
	d_proportions["trunk"] = trunk[0]
	d_proportions["primary"] = primary[0]
	d_proportions["secondary"] = secondary[0]
	d_proportions["tertiary"] = tertiary[0]
	d_proportions["unclassified"] = unclassified[0]
	d_proportions["residential"] = residential[0]
	d_proportions["service"] = service[0]

	class_piechart(d_proportions)
	plt.show()
	

if __name__ == "__main__":
	main()
