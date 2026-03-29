# Naming Conventions

## Methods/Functions: Verb-Noun Pattern

Methods and functions should clearly describe the action they perform.

### Java/Scala: camelCase

Before:
```
userData()              // What does this do? Get? Process? Validate?
data()                  // Too vague
process()               // Process what?
handleRequest()         // Generic, unclear outcome
```

After:
```
findUserById(id)        // Clear: finds a user by ID
validateOrderItems()    // Clear: validates order items
sendEmailNotification() // Clear: sends an email notification
calculateTotalPrice()   // Clear: calculates total price
```

### Python: snake_case

Before:
```python
def userData():         # Wrong case, unclear action
def data():             # Too vague
def process():          # Process what?
def handleRequest():    # Wrong case, generic
```

After:
```python
def find_user_by_id(user_id):    # Clear: finds a user by ID
def validate_order_items():       # Clear: validates order items
def send_email_notification():    # Clear: sends an email notification
def calculate_total_price():      # Clear: calculates total price
```

### Common Verb Prefixes

| Verb | Usage |
|------|-------|
| `find` / `get` | Retrieve data (find implies search, get implies direct access) |
| `create` / `build` | Construct new objects |
| `update` / `modify` | Change existing data |
| `delete` / `remove` | Remove data |
| `validate` / `verify` | Check correctness |
| `calculate` / `compute` | Perform calculations |
| `send` / `notify` | Communication actions |
| `parse` / `convert` | Transform data formats |
| `is` / `has` / `can` | Boolean queries |

## Classes: Nouns in PascalCase

Before:
```
usercontroller          // Wrong case
User_Controller         // Wrong separator
ProcessOrder            // Verb, not noun
```

After:
```
UserController          // PascalCase noun
OrderService            // Clear responsibility
PaymentGateway          // Descriptive noun
```

## Variables: Descriptive Names

Use descriptive names that convey purpose. Case convention varies by language.

### Java/Scala: camelCase

Before:
```
int x;                  // Meaningless
String s;               // Meaningless
List<User> list;        // Type, not purpose
User u;                 // Abbreviated
```

After:
```
int retryCount;         // Clear purpose
String emailAddress;    // Descriptive
List<User> activeUsers; // Purpose-driven
User currentUser;       // Context-aware
```

### Python: snake_case

Before:
```python
x = 0                   # Meaningless
s = ""                  # Meaningless
list = []               # Type, not purpose (also shadows built-in!)
u = None                # Abbreviated
```

After:
```python
retry_count = 0         # Clear purpose
email_address = ""      # Descriptive
active_users = []       # Purpose-driven
current_user = None     # Context-aware
```

## Constants: SCREAMING_SNAKE_CASE

Before:
```
static final int maxRetries = 3;        // Wrong case
static final String apiUrl = "...";     // Wrong case
```

After:
```
static final int MAX_RETRY_ATTEMPTS = 3;
static final String API_BASE_URL = "...";
static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(30);
```

## Boolean Naming

Boolean variables and methods should read as questions.

Before:
```
boolean active;         // Is it active? Should be active?
boolean check();        // Check what? Returns what?
```

After:
```
boolean isActive;       // Clear state question
boolean hasPermission;  // Clear possession question
boolean canExecute();   // Clear capability question
boolean shouldRetry();  // Clear decision question
```

## Avoid Abbreviations

Before:
```
calcTot()               // Unclear abbreviation
usrSvc                  // Hard to read
maxRetCnt               // Cryptic
```

After:
```
calculateTotal()        // Full words
userService             // Readable
maxRetryCount           // Clear meaning
```

**Exception**: Well-known domain abbreviations are acceptable:
- `id` (identifier)
- `url` (uniform resource locator)
- `http` / `https`
- `api` (application programming interface)
- Domain-specific terms established in the codebase
