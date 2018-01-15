import math

import rhinoscriptsyntax as rs

import compas_rhino as rhino

from compas.datastructures.mesh import Mesh

def custom_constraints(mesh, surface):
    from compas_pattern.cad.rhino.spatial_NURBS_input_to_planar_discrete_output import surface_borders
    
    #surface_boundaries = surface_borders(surface, border_type = 0)
    
    rs.EnableRedraw(True)
    surface_boundaries = rs.GetObjects('surface boundaries', filter = 4)
    rs.EnableRedraw(False)
    
    constraints = {}
    
    artist = rhino.MeshArtist(mesh, layer='mesh_artist')
    artist.clear_layer()
    
    vertex_dots = {rs.AddTextDot(vkey, mesh.vertex_coordinates(vkey)): vkey for vkey in mesh.vertices()}
    rs.EnableRedraw(True)
    fixed_vertices = rs.GetObjects('fixed vertices', filter = 8192)
    vkeys = [vertex_dots[vkey] for vkey in fixed_vertices]
    rs.DeleteObjects(vertex_dots)
    rs.EnableRedraw(False)
    #artist.draw_vertexlabels()
    #artist.redraw()
    #vkeys = rhino.mesh_select_vertices(mesh, message = 'fixed vertices')
    #artist.clear_layer()
    #artist.redraw()
    
    for vkey in vkeys:
        if vkey not in constraints:
            constraints[vkey] = ('fixed', mesh.vertex_coordinates(vkey)) 
    
    # collect boundayr polylines with splits
    from compas_pattern.topology.polyline_extraction import mesh_polylines_boundary
    mesh_boundaries = mesh_polylines_boundary(mesh)
    split_vertices = [vkey for vkey, constraint in constraints.items() if constraint[0] == 'fixed']

    # add one vertex per mesh boundary element that has no split vertices yet, i.e. that has no corner vertices (2-valency)
    for boundary in mesh_boundaries:
        to_add = True
        for vkey in boundary:
            if vkey in split_vertices:
                to_add = False
                break
        if to_add:
            split_vertices.append(boundary[0])
    
    
    split_mesh_boundaries = []
    while len(split_vertices) > 0:
        start = split_vertices.pop()
        # exception if split vertex corresponds to a non-boundary point feature
        if not mesh.is_vertex_on_boundary(start):
            continue
        polyline = [start]

        while 1:
            for nbr, fkey in iter(mesh.halfedge[polyline[-1]].items()):
                if fkey is None:
                    polyline.append(nbr)
                    break

            # end of boundary element
            if start == polyline[-1]:
                split_mesh_boundaries.append(polyline)
                break
            # end of boundary subelement
            elif polyline[-1] in split_vertices:
                split_mesh_boundaries.append(polyline)
                split_vertices.remove(polyline[-1])
                polyline = polyline[-1 :]
    
    srf_dots = {rs.AddTextDot('srf_boundary', rs.CurveMidPoint(srf_bdry)): srf_bdry for srf_bdry in surface_boundaries}
    
    for mesh_bdry in split_mesh_boundaries:
        if len(mesh_bdry) == 2:
            xyz = mesh.edge_midpoint(mesh_bdry[0], mesh_bdry[1])
        else:
            idx = int(math.floor(len(mesh_bdry) / 2))
            xyz = mesh.vertex_coordinates(mesh_bdry[idx])
        mesh_dot = rs.AddTextDot('?', xyz)
        
        rs.EnableRedraw(True)
        crv_cstr = srf_dots[rs.GetObject('boundary constraint', filter = 8192)]
        rs.EnableRedraw(False)
        
        for vkey in mesh_bdry:
            if vkey not in constraints:
                constraints[vkey] = ('curve', crv_cstr)
        
        
        rs.DeleteObject(mesh_dot)
    
    rs.EnableRedraw(True)
    rs.DeleteObjects(srf_dots)
    rs.EnableRedraw(False)
    
    for vkey in mesh.vertices():
        if vkey not in constraints:
            constraints[vkey] = ('surface', surface)
    
    return constraints, surface_boundaries

def start():
    from compas.geometry.algorithms.smoothing import mesh_smooth_centroid
    from compas.geometry.algorithms.smoothing import mesh_smooth_area
    
    from compas_pattern.algorithms.constrained_smoothing import define_constraints
    from compas_pattern.algorithms.constrained_smoothing import apply_constraints
    
    dense_mesh = rs.GetObject('mesh to smooth', filter = 32)
    dense_mesh = rhino.mesh_from_guid(Mesh, dense_mesh)
    
    surface_guid = rs.GetSurfaceObject('surface constraint')[0]
    
    smooth_mesh = dense_mesh.copy()
    
    smoothing_iterations = rs.GetInteger('number of iterations for smoothing', number = 20)
    damping_value = rs.GetReal('damping value for smoothing', number = .5)
    
    rs.EnableRedraw(False)
    
    constraints, surface_boundaries = custom_constraints(smooth_mesh, surface_guid)
    fixed_vertices = [vkey for vkey, constraint in constraints.items() if constraint[0] == 'fixed']
    mesh_smooth_area(smooth_mesh, fixed = fixed_vertices, kmax = smoothing_iterations, damping = damping_value, callback = apply_constraints, callback_args = [smooth_mesh, constraints])
    
    
    vertices = [smooth_mesh.vertex_coordinates(vkey) for vkey in smooth_mesh.vertices()]
    face_vertices = [smooth_mesh.face_vertices(fkey) for fkey in smooth_mesh.faces()]
    smooth_mesh_guid = rhino.utilities.drawing.xdraw_mesh(vertices, face_vertices, None, None)
    layer_name = 'smooth_mesh_4'
    rs.AddLayer(layer_name)
    rs.ObjectLayer(smooth_mesh_guid, layer = layer_name)
    
    rs.LayerVisible(layer_name, visible = True)
    
    rs.EnableRedraw(True)

start()