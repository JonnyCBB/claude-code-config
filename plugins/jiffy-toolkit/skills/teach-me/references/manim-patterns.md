# Manim Patterns

## Table of Contents
- Scene Template
- Common Animations
- ManimML Plugin Patterns
- Rendering Commands
- Output Directory Conventions
- File Embedding Patterns

## Scene Template

```python
from manim import *

class ConceptScene(Scene):
    def construct(self):
        # Title
        title = Text("Concept Name", font_size=48)
        self.play(Write(title))
        self.wait(0.5)
        self.play(title.animate.to_edge(UP).scale(0.6))

        # Main content
        # ... animations here ...

        self.wait(1)
```

Scene with custom colors matching the CSS design system:

```python
from manim import *

# Match CSS design system colors
PRIMARY = "#6366f1"
ACCENT = "#f59e0b"
BG = "#0f0f23"      # Dark theme background
TEXT_COLOR = "#e2e8f0"

class StyledScene(Scene):
    def construct(self):
        self.camera.background_color = BG
        text = Text("Hello", color=TEXT_COLOR, font_size=48)
        self.play(Write(text))
```

## Common Animations

**Create (draw stroke then fill):**
```python
circle = Circle(radius=1, color=PRIMARY)
self.play(Create(circle))
```

**Transform (morph one shape to another):**
```python
square = Square(side_length=2, color=PRIMARY)
circle = Circle(radius=1, color=ACCENT)
self.play(Transform(square, circle))
```

**FadeIn with direction:**
```python
box = Rectangle(width=3, height=1, color=PRIMARY)
self.play(FadeIn(box, shift=UP))
```

**Write (for text and LaTeX):**
```python
equation = MathTex(r"\nabla f(x) = \frac{\partial f}{\partial x}")
self.play(Write(equation))
```

**Indicate (pulse highlight):**
```python
self.play(Indicate(important_element, color=ACCENT))
```

**Succession (chain multiple animations):**
```python
self.play(
    Succession(
        Create(arrow1),
        Create(arrow2),
        Create(arrow3),
        lag_ratio=0.3
    )
)
```

**NumberLine with moving dot:**
```python
line = NumberLine(x_range=[-3, 3, 1], length=8)
dot = Dot(line.n2p(0), color=ACCENT)
self.play(Create(line), Create(dot))
self.play(dot.animate.move_to(line.n2p(2)), run_time=2)
```

## ManimML Plugin Patterns

Install: `pip install manim-ml`

**Neural Network:**
```python
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer

class NNScene(Scene):
    def construct(self):
        nn = NeuralNetwork([
            FeedForwardLayer(4),
            FeedForwardLayer(6),
            FeedForwardLayer(6),
            FeedForwardLayer(2),
        ])
        self.add(nn)
        self.play(nn.make_forward_pass_animation(), run_time=3)
```

**CNN:**
```python
from manim_ml.neural_network import NeuralNetwork, Convolutional2DLayer, FeedForwardLayer

class CNNScene(Scene):
    def construct(self):
        cnn = NeuralNetwork([
            Convolutional2DLayer(1, 8, 3),
            Convolutional2DLayer(8, 16, 3),
            FeedForwardLayer(128),
            FeedForwardLayer(10),
        ])
        self.add(cnn)
        self.play(cnn.make_forward_pass_animation(), run_time=5)
```

## Rendering Commands

```bash
# Medium quality GIF (recommended for teach-me)
manim -qm --format gif scene_file.py SceneClassName

# Medium quality WebM (smaller file, modern browsers)
manim -qm --format webm scene_file.py SceneClassName

# Low quality for quick preview
manim -ql --format gif scene_file.py SceneClassName

# High quality for final render
manim -qh --format gif scene_file.py SceneClassName
```

Quality flags:
- `-ql` — 480p, 15fps (fast preview)
- `-qm` — 720p, 30fps (good balance)
- `-qh` — 1080p, 60fps (high quality)
- `-qk` — 4K, 60fps (overkill for web)

Output location: `media/videos/<scene_file>/<quality>/SceneClassName.gif`

## Output Directory Conventions

The render_manim.py script handles output placement. Default Manim output structure:

```
media/
└── videos/
    └── scene_file/
        └── 720p30/
            └── SceneClassName.gif
```

The script copies the final output to the target directory:

```
~/.claude/teach-me/<slug>/
├── index.html
└── media/
    ├── gradient_descent.gif
    └── loss_landscape.gif
```

## File Embedding Patterns

**File reference (recommended for files > 100KB):**
```html
<img src="media/gradient_descent.gif" alt="Gradient descent animation"
     loading="lazy" width="600" height="400">
```

**Video reference (for WebM):**
```html
<video autoplay loop muted playsinline width="600" height="400">
  <source src="media/loss_landscape.webm" type="video/webm">
  <img src="media/loss_landscape.gif" alt="Fallback for browsers without WebM">
</video>
```

**Base64 data URI (only for files < 500KB, handled by embed_media.py):**
```html
<img src="data:image/gif;base64,R0lGODlh..." alt="Small animation">
```

Use the embed_media.py script to automatically convert small file references to base64:
```bash
python3 scripts/embed_media.py index.html --max-size 500000
```
