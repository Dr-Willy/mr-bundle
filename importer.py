import bpy

class OP_ImportBundle(bpy.types.Operator):
    bl_idname = "bundle.import"
    bl_label  = "Import Bundle.out"
    bl_description = "Import estimated cameras and point cloud from bundle.out"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    #filename = bpy.props.StringProperty(subtype="FILE_PATH")
    #directory= bpy.props.StringProperty(subtype="FILE_PATH")
    #files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    filter_glob = bpy.props.StringProperty(default="bundle.out", options={'HIDDEN'},)

    loadListFile = bpy.props.BoolProperty(name="Load Images", default=True)
    #listFilePath = bpy.props.StringProperty(name="listfile", default="listfile.txt", subtype="FILE_PATH")

    counter = 0
    bundleFile =""

    @classmethod
    def poll(cls, ctx):
        return True

    def execute(self, ctx):
        if self.counter == 0:
            self.bundleFile = self.filepath
            self.counter += 1
            print("bundle file =", self.bundleFile)
            if self.loadListFile:
                #self.loadListFile.options = {'HIDDEN'}
                self.bl_label = "Load Listfile.txt"
                self.filter_glob = "*.txt"
                ctx.window_manager.fileselect_add(self)
                return {'PASS_THROUGH'}
            else:
                print('loading without images')
                loadBundle(ctx.scene, self.bundleFile)
                return {'FINISHED'}

        listfile = self.filepath
        print('loading normally')
        print(listfile)
        loadBundle(ctx.scene, self.bundleFile, listfile)
        return {'FINISHED'}

    def invoke(self, ctx, event):
        print("context =", ctx)
        ctx.window_manager.fileselect_add(self)
        #ctx.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

def loadBundle(sc, fbundle, flistimg=None):
    from .utils.other import Camera,Point,Feature
    from .utils.bundle import Bundle

    import mathutils

    def gen():
        i=0
        while True:
            yield "{:05d}".format(i)
            i+=1

    camNames = gen()
    if flistimg:
        with open(flistimg, 'r') as f:
            lines = f.readlines()
            camNames = [ l.split()[0] for l in lines ]
        camNames = [ n.strip(' \n\t\r') for n in camNames ]

    bundle = Bundle( fbundle, camNames)

    for i,cam_ in enumerate(bundle.cameras):
        cam = Camera(*cam_)
        cname = 'bCam{:03d}'.format(i)
        camera = bpy.data.cameras.new(cname)
        obj = bpy.data.objects.new(cname, camera)

        camera.sensor_width = 1920.0
        camera.lens = cam.focal
        print("rot =", cam.rotation)
        R = mathutils.Matrix(cam.rotation).to_4x4()
        t = mathutils.Vector( (*cam.translation,1) )
        T = mathutils.Matrix.Translation( -t )

        obj.matrix_world = R.transposed() * T
        obj['pseudo'] = cam.name

        sc.objects.link(obj)

    me = bpy.data.meshes.new('point cloud')
    me.vertices.add(len(bundle.points))
    for i,pts_ in enumerate(bundle.points):
        pts = Point(*pts_)
        me.vertices[i].co = pts.pos

    obj = bpy.data.objects.new("BundlePoints", me)
    sc.objects.link(obj)






def import_menu_func(self, ctx):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(OP_ImportBundle.bl_idname, text=OP_ImportBundle.bl_label)

def register():
    bpy.utils.register_class(OP_ImportBundle)
    bpy.types.INFO_MT_file_import.append(import_menu_func)

def unregister():
    bpy.utils.unregister_class(OP_ImportBundle)
    bpy.types.INFO_MT_file_import.remove(import_menu_func)

