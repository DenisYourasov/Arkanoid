from tkinter import *
from time import perf_counter
from random import randint, randrange
from math import sqrt
from PIL import Image,ImageTk


class Vector2:
	def __init__(self, x, y):
		self.x = x
		self.y = y

def cross_prod(a, b):
	return a.x * b.y - b.x * a.y

def fromDifferentSides(main, v1, v2):
	product1 = cross_prod(main, v1)
	product2 = cross_prod(main, v2)
	return (product1 >= 0 and product2 <= 0 or product1 <= 0 and product2 >= 0)

def vectorFrom2Dots(d1, d2):
	return Vector2(d2.x - d1.x, d2.y - d1.y)

def linesIntersect(a, b, c, d):
	main = vectorFrom2Dots(a, b)
	v1 = vectorFrom2Dots(a, c)
	v2 = vectorFrom2Dots(a, d)

	if fromDifferentSides(main,v1,v2):
		main = vectorFrom2Dots(c, d)
		v1 = vectorFrom2Dots(c, a)
		v2 = vectorFrom2Dots(c, b)
		return fromDifferentSides(main, v1, v2)

	return False

def sign(x):
	return x / abs(x)


class Effect:
	def __init__(self, ball, platform):
		self.ball = ball
		self.platform = platform

	def activate(self):
		# run effect timer
		pass

	def deactivate(self):
		pass

	def update(self, delta):
		# check effect timer and self deactivate
		pass


class FireballEffect(Effect):
	def activate(self):
		self.fireHandle = app.canvas.create_image(10, 300, image=app.fireballImageHandle)
		self.ball.updateVisual(self.fireHandle)

	def deactivate(self):
		self.ball.updateVisual(None)


class Block:
	def __init__(self, canvas, position, size, outline, fill):
		self.canvas = canvas
		self.position = position
		self.size = size
		self.handle = self.canvas.create_rectangle(self.position[0], self.position[1], self.position[0] + self.size[0], self.position[1] + self.size[1], outline=outline, fill=fill)

	def checkHit(self):
		pass

	def onHit(self):
		self.destroy()

	def destroy(self):
		self.canvas.delete(self.handle)

		# Spawn bonus
		probability = 20
		value = randrange(0, 100)

		if value < probability:
			# really spawn bonus
			bonus = Bonus(self.canvas, self.position)
			app.gameState.bonuses.append(bonus)



class BlockGenerator:
	def spawnBlocks(self, canvas, canvasSize):
		pass


class RectBlockGenerator(BlockGenerator):
	def __init__(self):
		self.colorBlocksList = ('red', 'green', 'blue', 'orange', 'black')

	def spawnBlocks(self, canvas, canvasSize):
		result = []
		rows = 5
		columns = 25
		blockSize = (int(canvasSize[0] / columns), 25)

		for y in range(rows):
			for x in range(columns):
				position = (x * blockSize[0], y * blockSize[1])
				color = self.colorBlocksList[randint(0, len(self.colorBlocksList) - 1)]
				block = Block(canvas, position, blockSize, 'white', color)
				result.append(block)

		return result


class BlockManager:
	def __init__(self, canvas, canvasSize, generator):
		self.canvas = canvas
		self.canvasSize = canvasSize
		self.generator = generator
		self.blocks = []

	def spawnBlocks(self):
		self.blocks = self.generator.spawnBlocks(self.canvas, self.canvasSize)

	# Query if ball movement during next frame will collide with any block
	# return list of intersections
	def queryBlocksCollision(self, ball):
		dt = app.deltaTime
		speedMagnitude = sqrt(ball.speed[0] * ball.speed[0] + ball.speed[1] * ball.speed[1])

		if speedMagnitude < 0.0001:
			return []

		offset = [ball.speed[0] / speedMagnitude * ball.radius, ball.speed[1] / speedMagnitude * ball.radius]
		ballPos = Vector2(ball.position[0], ball.position[1])
		ballTarget = Vector2(ball.position[0] + ball.speed[0] * dt + offset[0], ball.position[1] + ball.speed[1] * dt + offset[1])
		intersections = []

		# TODO: Don't interate over all blocks, iterate only over reachable

		for block in self.blocks:
			blockPoints = [
				Vector2(block.position[0], block.position[1]),
				Vector2(block.position[0] + block.size[0], block.position[1]),
				Vector2(block.position[0] + block.size[0], block.position[1] + block.size[1]),
				Vector2(block.position[0], block.position[1] + block.size[1]),
			]

			blockLines = [
				(blockPoints[0], blockPoints[1]), # TOP
				(blockPoints[1], blockPoints[2]), # RIGHT
				(blockPoints[2], blockPoints[3]), # BOTTOM
				(blockPoints[0], blockPoints[3]), # LEFT
			]

			sideNames = [ 'TOP', 'RIGHT', 'BOTTOM', 'LEFT' ]

			for i in range(4):
				line = blockLines[i]
				if linesIntersect(line[0], line[1], ballPos, ballTarget):
					intersections.append({ 'block': block, 'side': sideNames[i] })

		return intersections

	def destroyBlock(self, block):
		block.onHit()
		self.blocks.remove(block)


class Bonus:
	def __init__(self, canvas, position):
		self.canvas = canvas
		self.platform = app.gameState.platform
		self.position = [ position[0], position[1] ]
		self.speed = 250
		self.radius = 15
		self.handle = canvas.create_oval(self.position[0] - self.radius, self.position[1] - self.radius, self.position[0] + self.radius, self.position[1] + self.radius, outline='green', fill='green')

	def update(self, delta):
		# Apply speed to position
		self.position[1] = self.position[1] + self.speed * delta

		self.handlePlatformCollision()
		
		self.canvas.moveto(self.handle, int(self.position[0] - self.radius), int(self.position[1] - self.radius))

	def handlePlatformCollision(self):
		bottomBorder = app.canvasSize[1] - self.platform.size[1] - self.radius
		if (self.position[1] > bottomBorder):
			leftBorder = self.platform.positionX - self.radius
			rightBorder = self.platform.positionX + self.platform.size[0] + self.radius
			if (self.position[0] >= leftBorder) and (self.position[0] <= rightBorder):
				# Use random bonus effect, add it to game state
				effect = FireballEffect(app.gameState.ball, app.gameState.platform)
				app.gameState.activateEffect(effect)
				
				self.destroy()
			else:
				killY = app.canvasSize[1] - self.radius
				if (self.position[1] > killY):
					self.destroy()

	def destroy(self):
		self.canvas.delete(self.handle)
		app.gameState.bonuses.remove(self)


class Ball:
	def __init__(self, canvas, canvasSize, platform, blockManager):
		self.canvas = canvas
		self.position = [105, 105]
		self.speed = [200, 200]
		self.canvasSize = canvasSize
		self.radius = 15
		self.platform = platform
		self.blockManager = blockManager

		self.fireMode = False
		self.allowMovement = True

		# configure visual
		#image = Image.open("fireball.png")
		#image = image.resize((self.radius * 2, self.radius * 2), Image.ANTIALIAS)
		#self.pic = ImageTk.PhotoImage(image)
		#self.fireHandle = canvas.create_image(10, 300, image=self.pic)
		self.defaultHandle = canvas.create_oval(self.position[0] - self.radius, self.position[1] - self.radius, self.position[0] + self.radius, self.position[1] + self.radius, outline='red', fill='red')
		self.handle = self.defaultHandle

		#self.updateVisual()

	def update(self, delta):
		# Apply speed to position
		if self.allowMovement:
			self.position[0] = self.position[0] + self.speed[0] * delta
			self.position[1] = self.position[1] + self.speed[1] * delta

			self.handleBlocksCollision()
			self.handlePlatformCollision()
			self.handleFrameCollision()

		#self.updateVisual()
		self.canvas.moveto(self.handle, int(self.position[0] - self.radius), int(self.position[1] - self.radius))

	def updateVisual(self, handle):
		if handle:
			if self.handle:
				self.canvas.itemconfigure(self.handle, state='hidden')

			self.handle = handle
		else:
			self.handle = self.defaultHandle

		self.canvas.itemconfigure(self.handle, state='normal')

		#if self.fireMode:
		#	self.handle = self.fireHandle
		#	self.canvas.itemconfigure(self.defaultHandle, state='hidden')
		#else:
		#	self.handle = self.defaultHandle
		#	self.canvas.itemconfigure(self.fireHandle, state='hidden')

		# Move visual element to logical position
		#self.canvas.itemconfigure(self.handle, state='normal')
		#self.canvas.moveto(self.handle, int(self.position[0] - self.radius), int(self.position[1] - self.radius))

	def handlePlatformCollision(self):
		bottomBorder = self.canvasSize[1] - self.platform.size[1] - self.radius
		if (self.position[1] > bottomBorder) and self.speed[1] > 0:
			leftBorder = self.platform.positionX - self.radius
			rightBorder = self.platform.positionX + self.platform.size[0] + self.radius
			if (self.position[0] >= leftBorder) and (self.position[0] <= rightBorder):
				self.platform.onHit(self)

				self.speed[1] = -self.speed[1]
				overflow = self.position[1] - bottomBorder
				self.position[1] = bottomBorder - overflow
			else:
				killY = self.canvasSize[1] - self.radius
				if (self.position[1] > killY):
					app.gameState.onGameOver()

	def handleFrameCollision(self):
		# Handle frame collisions
		for axis in range(2):
			leftBorder = self.radius
			rightBorder = self.canvasSize[axis] - self.radius

			if (self.position[axis] < leftBorder) and self.speed[axis] < 0:
				self.speed[axis] = -self.speed[axis]
				overflow = leftBorder - self.position[axis]
				self.position[axis] = leftBorder + overflow

			if (self.position[axis] > rightBorder) and self.speed[axis] > 0:
				self.speed[axis] = -self.speed[axis]
				overflow = self.position[axis] - rightBorder
				self.position[axis] = rightBorder - overflow

	def handleBlocksCollision(self):
		intersections = self.blockManager.queryBlocksCollision(self)

		if len(intersections) > 0:
			intersection = intersections[0]

			# mirror speed
			if not self.fireMode:
				if intersection['side'] == 'BOTTOM' or intersection['side'] == 'TOP':
					self.speed[1] = -self.speed[1]
				else:
					self.speed[0] = -self.speed[0]

			# destroy block
			self.blockManager.destroyBlock(intersection['block'])

			self.fireMode = True
		elif len(intersections) > 1:
			print('intersect multiple')


class Platform:
	def __init__(self, canvas, canvasSize):
		self.canvas = canvas
		self.canvasSize = canvasSize
		self.size = [ 200, 10 ]
		self.positionX = (self.canvasSize[0] - self.size[0]) * 0.5
		self.positionY = self.canvasSize[1] - self.size[1]
		self.playerLimits = (0, canvasSize[0] - self.size[0])
		self.holdState = None
		self.speed = 400 # Pixels per second
		self.keysPressed = dict()
		self.handle = self.canvas.create_rectangle(self.positionX, canvasSize[1] - self.size[1], self.positionX + self.size[0], canvasSize[1], outline='black', fill='grey')

	def keypress(self, event):
		self.keysPressed[event.keycode] = True

	def keyrelease(self, event):
		self.keysPressed[event.keycode] = False

	def update(self, delta):
		# Add movement
		deltaX = 0
		if self.keysPressed.get(65) or self.keysPressed.get(37): deltaX = deltaX - self.speed * delta
		if self.keysPressed.get(68) or self.keysPressed.get(39): deltaX = deltaX + self.speed * delta

		self.positionX = self.positionX + deltaX
		self.positionX = min(max(self.playerLimits[0], self.positionX), self.playerLimits[1])

		self.canvas.moveto(self.handle, int(self.positionX), self.positionY)

		# Hold state can stick the ball to the platform temporary, and ball will move with platform
		if self.holdState != None:
			self.holdState['ball'].position = [
				self.positionX + self.holdState['offset'][0], self.positionY + self.holdState['offset'][1]
			]

			if self.holdState['mode'] == 'timer':
				self.holdState['time'] = self.holdState['time'] - delta

				# release the ball
				if self.holdState['time'] < 0:
					# tweak ball speed vector
					offset = self.positionX - self.holdState['platformPos']
					self.holdState['ball'].speed[0] = self.holdState['ball'].speed[0] + offset

					self.holdState['ball'].allowMovement = True
					self.holdState = None
			elif self.holdState['mode'] == 'manual':
				if self.keysPressed.get(65):
					# release the ball
					self.holdState['ball'].allowMovement = True
					self.holdState = None

	def onHit(self, ball):
		ball.allowMovement = False
		self.holdState = {
			'mode': 'timer',
			'ball': ball,
			'offset': [ball.position[0] - self.positionX, ball.position[1] - self.positionY],
			'time': 0.075,
			'platformPos': self.positionX,
		}

	def holdBallOnStart(self, ball):
		ball.allowMovement = False
		self.holdState = {
			'mode': 'manual',
			'ball': ball,
			'offset': [ball.position[0] - self.positionX, ball.position[1] - self.positionY],
		}


class GameState:
	def __init__(self, canvas, canvasSize):
		self.canvas = canvas
		self.canvasSize = canvasSize
		self.gameStarted = True
		self.gameOver = False
		self.pause = False

		blockGenerator = RectBlockGenerator()
		self.blockManager = BlockManager(self.canvas, self.canvasSize, blockGenerator)
		self.blockManager.spawnBlocks()

		self.platform = Platform(self.canvas, canvasSize)
		self.ball = Ball(self.canvas, canvasSize, self.platform, self.blockManager)
		self.ball.position = [self.platform.positionX + self.platform.size[0] * 0.5, self.platform.positionY - self.ball.radius]
		self.platform.holdBallOnStart(self.ball)

		self.bonuses = []
		self.effects = []

		# создаем надпись
		self.deathMessage = Label(master=self.canvas, text = 'Game Over!', font = ('bold', 30), fg='black', bg='red')
		#self.deathMessage.place_forget()

	def onGameOver(self):
		self.deathMessage.place(x=100,y=100)
		self.gameOver = True

	def activateEffect(self, effect):
		self.effects.append(effect)
		effect.activate()

	def deactivateEffect(self, effect):
		effect.deactivate()
		self.effects.remove(effect)

	def update(self, deltaTime):
		if not self.gameOver:
			self.platform.update(deltaTime)
			self.ball.update(deltaTime)

			for bonus in self.bonuses:
				bonus.update(deltaTime)

			for effect in self.effects:
				effect.update(deltaTime)


class App:
	def __init__(self):
		# создаем родительское окно
		self.root = Tk()
		self.root.title('ARKANOID')
		#self.root.geometry('800x600')
		self.root.attributes("-fullscreen", True)
		#self.root.geometry("{0}x{1}+0+0".format(self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
		#Tk.attributes("-fullscreen", True)

		# Load image resources
		self.fireballImage = Image.open("fireball.png")
		self.fireballImage = self.fireballImage.resize((30, 30), Image.ANTIALIAS)
		self.fireballImageHandle = ImageTk.PhotoImage(self.fireballImage)

		# создадим канвас
		self.canvas = Canvas(self.root, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
		self.canvas.place(x=0,y=0)
		self.canvasSize = ( self.root.winfo_screenwidth(), self.root.winfo_screenheight() )

		self.gameState = GameState(self.canvas, self.canvasSize)

		# обработчик клавиш
		def keypress(event):
			self.gameState.platform.keypress(event)

		def keyrelease(event):
			self.gameState.platform.keyrelease(event)
		
		#self.root.bind("<Key>", keypress)
		self.root.bind('<KeyPress>', keypress)
		self.root.bind('<KeyRelease>',keyrelease)

		# Организуем цикл выполнения программы
		self.closeRequested = False

		def onWindowClose():
			self.closeRequested = True

		self.root.protocol('WM_DELETE_WINDOW', onWindowClose)

		self.lastUpdateTime = perf_counter()

	def update(self):
		# Update delta time
		timestamp = perf_counter()
		self.deltaTime = timestamp - self.lastUpdateTime
		self.lastUpdateTime = timestamp

		self.gameState.update(self.deltaTime)

	def render(self):
		pass

	def mainLoop(self):
		while not self.closeRequested:
			self.root.update_idletasks()
			self.root.update()
			self.update()
			self.render()

app = App()
app.mainLoop()

# 1. Запуск шарика в начале +
# 2. Полноэкранный режим +
# 3. Блоки-бонусы 
# 4. Изменение скорости платформы
# 5. Изменение скорости шарика
# 6. Блоки, которые не разбиваются с первого раза
