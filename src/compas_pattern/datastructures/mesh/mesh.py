from compas.datastructures.mesh import Mesh

from compas.geometry import angle_points

from compas.utilities import geometric_key
from compas.utilities import pairwise


__all__ = ['Mesh']


### TO BE PUSHED TO COMPAS ###


class Mesh(Mesh):

	def __init__(self):
		super(Mesh, self).__init__()

	def to_vertices_and_faces(self, keep_keys=True):

		if keep_keys:
			vertices = {vkey: self.vertex_coordinates(vkey) for vkey in self.vertices()}
			faces = {fkey: self.face_vertices(fkey) for fkey in self.faces()}
		else:
			key_index = self.key_index()
			vertices = [self.vertex_coordinates(key) for key in self.vertices()]
			faces = [[key_index[key] for key in self.face_vertices(fkey)] for fkey in self.faces()]
		return vertices, faces

	def is_boundary_vertex_kink(self, vkey, threshold_angle):
		"""Return whether there is a kink at a boundary vertex according to a threshold angle.

		Parameters
		----------
		vkey : Key
			The boundary vertex key.
		threshold_angle : float
			Threshold angle in rad.

		Returns
		-------
		bool
			True if vertex is on the boundary and has an angle larger than the threshold angle. False otherwise.
		"""	
		
		# check if vertex is on boundary
		if not self.is_vertex_on_boundary(vkey):
			return False

		# get the two adjacent boundary vertices (exactly two for manifold meshes)
		ukey, wkey = [nbr for nbr in self.vertex_neighbors(vkey) if self.is_edge_on_boundary(vkey, nbr)]

		# compare boundary angle with threshold angle
		return angle_points(self.vertex_coordinates(ukey), self.vertex_coordinates(vkey), self.vertex_coordinates(wkey)) > threshold_angle

	def boundary_kinks(self, threshold_angle):
		"""Return the boundary vertices with kinks.

		Parameters
		----------
		threshold_angle : float
			Threshold angle in rad.

		Returns
		-------
		list
			The list of the boundary vertices at kink angles higher than the threshold value.

		"""

		return [vkey for vkey in self.vertices_on_boundary() if self.is_boundary_vertex_kink(vkey, threshold_angle)]


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

	import compas

	mesh = Mesh.from_obj(compas.get('faces.obj'))
