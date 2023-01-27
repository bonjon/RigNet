import bpy

def loadInfo(info_name, geo_name):
    armature = bpy.data.armatures.new("armature")
    rigged_model = bpy.data.objects.new("rigged_model", armature)
    
    bpy.context.collection.objects.link(rigged_model)
    bpy.context.view_layer.objects.active = rigged_model
    bpy.ops.object.mode_set(mode='EDIT')
    
    f_info = open(info_name,'r')
    joint_pos = {}
    joint_hier = {}
    joint_skin = []
    for line in f_info:
        word = line.split()
        if word[0] == 'joints':
            joint_pos[word[1]] = [float(word[2]),  float(word[3]), float(word[4])]
        if word[0] == 'root':
            root_pos = joint_pos[word[1]]
            root_name = word[1]

        if word[0] == 'hier':
            if word[1] not in joint_hier.keys():
                joint_hier[word[1]] = [word[2]]
            else:
                joint_hier[word[1]].append(word[2])
        if word[0] == 'skin':
            skin_item = word[1:]
            joint_skin.append(skin_item)
    f_info.close()
    
    print(joint_hier)
    
    current_mesh = bpy.context.selected_objects[0]
    
    this_level = [root_name]
    while this_level:
        next_level = []
        for node in this_level:
            print(f'Looking at {node}')
            pos = joint_pos[node]
            bone = armature.edit_bones.new(node)
            bone.head.x, bone.head.y, bone.head.z = pos[0], pos[1], pos[2]
            
            if bone.name not in current_mesh.vertex_groups:
                current_mesh.vertex_groups.new(name=bone.name)
            
            
            is_child = False
            is_parent = node in joint_hier.keys()
            
            if is_parent:
                x_distance = [abs(joint_pos[c][0] - pos[0]) for c in joint_hier[node]]
                
                print(x_distance)
                nearest_child_idx = x_distance.index(min(x_distance))
                nearest_child_pos = joint_pos[joint_hier[node][nearest_child_idx]]
                
                bone.tail.x, bone.tail.y, bone.tail.z = nearest_child_pos[0], nearest_child_pos[1], nearest_child_pos[2]
                
                for c_node in joint_hier[node]:
                    next_level.append(c_node)
            else:
                for parent, children in joint_hier.items():
                    if node in children:
                        is_child = True
                        bone.parent = armature.edit_bones[parent]
                        offset = bone.head - bone.parent.head
                        bone.tail = bone.head + offset / 2
                        break
                
                if not is_child:
                    # This node not is neither a parent nor a child
                    bone.tail.x, bone.tail.y, bone.tail.z = pos[0], pos[1], pos[2]
                    bone.tail.y += 0.1
                    
        this_level = next_level         
        
    print(joint_skin)
    bpy.ops.object.mode_set(mode='POSE')
    for v_skin in joint_skin:
        v_idx = int(v_skin.pop(0))
        
        for i in range(0, len(v_skin), 2):
            current_mesh.vertex_groups[v_skin[i]].add([v_idx], float(v_skin[i + 1]), 'REPLACE')

    rigged_model.matrix_world = current_mesh.matrix_world
    rigged_model.location.xyz = 0
    mod = current_mesh.modifiers.new('rignet', 'ARMATURE')
    mod.object = rigged_model

        
    #cmds.joint(root_name, e=True, oj='xyz', sao='yup', ch=True, zso=True)
    #cmds.skinCluster( root_name, geo_name)
    #print len(joint_skin)
    #for i in range(len(joint_skin)):
    #    vtx_name = geo_name + '.vtx['+joint_skin[i][0]+']'
    #    transValue = []
    #    for j in range(1,len(joint_skin[i]),2):
    #        transValue_item = (joint_skin[i][j], float(joint_skin[i][j+1]))
    #        transValue.append(transValue_item) 
        #print vtx_name, transValue
        #cmds.skinPercent( 'skinCluster1', vtx_name, transformValue=transValue)
    #cmds.skinPercent( 'skinCluster1', geo_name, pruneWeights=0.01, normalize=False )
    return root_name, joint_pos


def getMeshOrigin():
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    
    # for geo in geometries:
    #     if 'ShapeOrig' in geo:
    #         '''
    #         we can also use cmds.ls(geo, l=True)[0].split("|")[0]
    #         to get the upper level node name, but stick on this way for now
    #         '''
    #         geo_name = geo.replace('ShapeOrig', '')
    #         geo_list.append(geo_name)
    # if not geo_list:
    #     geo_list = cmds.ls(type='surfaceShape')
    return bpy.context.selected_objects[0]


if __name__ == '__main__':
    model_id = "smith"
    print(model_id)
    obj_name = 'quick_start/{:s}_ori.obj'.format(model_id)
    info_name = 'quick_start/{:s}_ori_rig.txt'.format(model_id)
    out_name = 'quick_start/{:s}.gltf'.format(model_id)

    # parser = argparse.ArgumentParser(
    #                     prog = 'ProgramName',
    #                     description = 'What the program does',
    #                     epilog = 'Text at the bottom of help')
    # parser.add_argument('obj_name')
    # parser.add_argument('info_name')
    # parser.add_argument('-o', '--output')
    # args = parser.parse_args()
    #
    # print(args)

       
    # import obj
    bpy.ops.import_scene.obj(filepath=obj_name)
    # cmds.file(new=True,force=True)
    # cmds.file(obj_name, o=True)

    mesh = getMeshOrigin()
    #mesh.location.xyz = 0
    #mesh.location.y = 7.5
    #mesh.rotation_euler = (0, 0, 0)

    # import info
    root_name, _ = loadInfo(info_name, getMeshOrigin())
    
    # export fbx
    bpy.ops.export_scene.gltf(filepath=out_name)
