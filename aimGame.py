from panda3d.core import loadPrcFileData

loadPrcFileData("", "Config.prc")
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from panda3d.core import AmbientLight, DirectionalLight, LVector3, BitMask32
from panda3d.core import WindowProperties
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
import random
import sys
from panda3d.core import LineSegs, NodePath, CardMaker, LColor
class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Sensitivity setting
        self.sensitivity = 0.015
        # Set full-screen mode with high resolution
        props = WindowProperties()
        props.setFullscreen(True)
        props.setSize(1920, 1080)  # Set to your desired resolution
        self.win.requestProperties(props)
        #load sound
        self.hitSound = self.loader.loadSfx("sounds/hit2.wav")
        # Disable the default mouse-based camera control
        self.disableMouse()
        
        # Lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.2, 0.2, 0.2, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)
        
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(-5, -5, -5))
        directionalLight.setColor((0.8, 0.8, 0.8, 1))
        directionalLightNP = self.render.attachNewNode(directionalLight)
        self.render.setLight(directionalLightNP)
        
        # Add tasks
        self.taskMgr.add(self.update, "update")
        
        # Initialize balls
        self.balls = []
        self.grid_size = 3
        self.spawnBallsInGrid()
        
        # Collision traverser
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        
        # Collision ray for picking
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
        # Add mouse click event
        self.accept('mouse1', self.shoot)
        
        # Camera positioning
        self.camera.setPos(0, -20, 4)
        self.camera.lookAt(0, 0, 0)
        
        # Set up mouse look
        self.win.setClearColor((0, 0, 0, 1))
        self.centerMouse()
        self.disableMouse()
        self.accept("escape", sys.exit)  # Press escape to exit
        
        self.prevMousePos = None
        self.cameraPitch = 0
        self.cameraYaw = 0
        
        # Add crosshair
        self.crosshair = OnscreenImage(image='models/crosshair.png', pos=(0, 0, 0), scale=0.15)
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)

        #Draw
        self.createGrid()

        #For SpawnBall
        self.occupied_positions = set()


    def createGrid(self):
        # Initialize grid parameters
        grid_size = 7  # Number of cells per side
        cell_size = 2.0  # Size of each cell
        
        # Create a NodePath to hold the grid
        grid_node = NodePath("grid")
        
        # Create the white plane
        cm = CardMaker("grid_plane")
        cm.setFrame(-grid_size * cell_size / 2, grid_size * cell_size / 2, -grid_size * cell_size / 2, grid_size * cell_size / 2)
        plane = grid_node.attachNewNode(cm.generate())
        plane.setColor(LColor(3, 3, 3, 3))  # White color for the plane
        
        # Create the red borders
        line = LineSegs()
        line.setColor(1, 0, 0, 1)  # Red color for the borders
        
        # Draw borders around the grid
        half_size = (grid_size * cell_size) / 2
        line.moveTo(-half_size, 0, -half_size)  # Bottom-left corner
        line.drawTo(half_size, 0, -half_size)   # Bottom-right corner
        line.drawTo(half_size, 0, half_size)    # Top-right corner
        line.drawTo(-half_size, 0, half_size)   # Top-left corner
        line.drawTo(-half_size, 0, -half_size)  # Back to Bottom-left corner
        
        grid_borders = grid_node.attachNewNode(line.create())
        
        # Reparent the grid to render
        grid_node.reparentTo(self.render)

    def centerMouse(self):
        wp = WindowProperties()
        wp.setCursorHidden(True)
        self.win.requestProperties(wp)
    
    def spawnBallsInGrid(self):
        spacing = 2.0  # Adjust spacing as needed
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.spawnBall(i, j, spacing)
    
    def spawnBall(self, i=None, j=None, spacing=2.0):
        grid_size = 5  # Adjust according to your grid size
        cell_size = 2.0  # Adjust according to your cell size
        
        ball = self.loader.loadModel("models/ball.egg")
        ball.reparentTo(self.render)
        ball.setScale(0.5)
        
        if i is None or j is None:
            # Randomly choose a grid position that is not occupied
            available_positions = [(x, y) for x in range(grid_size) for y in range(grid_size) if (x, y) not in self.occupied_positions]
            if not available_positions:
                self.occupied_positions.clear()  # Clear the set if all positions are occupied
                available_positions = [(x, y) for x in range(grid_size) for y in range(grid_size)]
            grid_x, grid_y = random.choice(available_positions)
        else:
            grid_x, grid_y = i, j
        
        # Calculate position based on grid cell and cell size
        x = (grid_x - grid_size / 2) * cell_size
        z = (grid_y - grid_size / 2) * cell_size  # Use Z-axis instead of Y-axis
        ball.setPos(x, 0, z)  # Set Y to 0 and adjust X and Z
        
        ball.setTag('ball', str(id(ball)))  # Set a unique tag based on ball's ID
        ball.setCollideMask(BitMask32.bit(1))
        self.balls.append(ball)
    
    def update(self, task):
        """This task updates the mouse """
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, int(base.win.getXSize()/2), int(base.win.getYSize()/2)):
            base.camera.setH(base.camera.getH() - (x - base.win.getXSize()/2) * self.sensitivity)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2) * self.sensitivity)
        return task.cont
    
    def shoot(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            
            self.picker.traverse(self.render)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                pickedObj = self.pq.getEntry(0).getIntoNodePath()
                print("You hit the ball !")
                # Calculate the grid position of the hit ball
                hit_pos = pickedObj.getPos()
                grid_x = int((hit_pos.getX() + (self.grid_size / 2 * 2.0)) / 2.0)
                grid_y = int((hit_pos.getZ() + (self.grid_size / 2 * 2.0)) / 2.0)
                self.occupied_positions.discard((grid_x, grid_y))

                pickedObj.removeNode()
                self.hitSound.play()
                
                # Spawn a new ball at a random position in the grid
                self.spawnBall()
                
                
app = MyApp()
app.run()
