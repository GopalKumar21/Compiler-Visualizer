# C Compiler Visualizer

## Overview
This is a web-based C Compiler Visualizer built using Python and Flask. It allows users to input simple C code and visualize the compilation process through its various phases: lexical analysis, syntax analysis, semantic analysis, intermediate code generation, optimization, and assembly code generation. The application is designed for educational purposes, demonstrating how a compiler processes code step-by-step.

## Features
- **Code Input**: Enter C-like code (supporting `int` declarations, assignments, `for` loops, and `return` statements) in a web interface.
- **Compilation Phases**:
  - **Lexical Analysis**: Tokenizes the input code into keywords, operators, literals, and identifiers.
  - **Syntax Analysis**: Builds an Abstract Syntax Tree (AST) for declarations, assignments, `for` loops, and `return` statements.
  - **Semantic Analysis**: Checks for errors like variable redeclarations or undeclared variables.
  - **Intermediate Code Generation**: Produces intermediate code for assignments and returns.
  - **Optimization**: Placeholder for code optimization (currently copies intermediate code).
  - **Assembly Code Generation**: Generates simplified x86 assembly code for visualization.
- **Output Display**: Shows tokens, AST, intermediate code, optimized code, and assembly code for the input.
- **Error Handling**: Displays syntax or semantic errors with line numbers if the input code is invalid.

## Technologies Used
- Python 3.x
- Flask (web framework)
- Regular Expressions (`re`, standard library for lexical analysis)
- Logging (`logging`, standard library for debugging)
- HTML, Jinja2 (for templating)
- JavaScript (required but not implemented for frontend interaction)

## Prerequisites
Before running the application, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- A web browser (e.g., Chrome, Firefox)



## Usage
- **Access the Interface**: Open `http://localhost:5000` to view the web interface.
- **Enter Code**: Input C-like code in the provided textarea (e.g., `int main() { int x = 5; return x; }`).
- **Run Code**: Click the "Run Code" button to compile the code and view the output of each compilation phase (tokens, AST, intermediate code, optimized code, assembly code).
- **Clear Input**: Click the "Clear" button to reset the input and output areas.
- **View Errors**: If the code contains errors (e.g., syntax errors, undeclared variables), they will be displayed with line numbers.

### Example Input
```c
int main() {
    int x = 5;
    int y = x + 3;
    return y;
}
```
**Output**: Displays tokens, AST, intermediate code, optimized code, and assembly code for the input.

## Project Structure
```plaintext
├── app.py                    # Main Flask application
├── templates/                # HTML templates
│   ├── index.html            # Web interface for code input and output
├── README.md                 # This file
```

## Supported C Subset
The compiler visualizer supports a limited subset of C, including:
- Variable declarations (`int x;`, `int x = 5;`)
- Assignments (`x = 5;`, `x = y + 3;`)
- `for` loops (`for (int i = 0; i < 10; i++) { ... }`)
- Function declarations (`int main() { ... }`)
- `return` statements (`return x;`)
- Basic arithmetic operators (`+`, `*`)

## Known Issues
- The `index.html` template lacks JavaScript to handle the "Run Code" button and send code to the `/run` endpoint. You need to add JavaScript (e.g., using `fetch`) to make the interface functional. Example:
  ```html
  <script>
      async function runCode() {
          const code = document.querySelector('#code-input').value;
          const response = await fetch('/run', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code })
          });
          const result = await response.json();
          document.querySelector('#output').innerText = result.output;
      }
  </script>
  ```
- The `index.html` template is incomplete, missing `<html>`, `<head>`, and `<body>` tags. Add these for proper rendering:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>C Compiler Visualizer</title>
  </head>
  <body>
      <!-- Existing content -->
  </body>
  </html>
  ```
- No CSS styling is applied to `index.html`. Consider adding Bootstrap or custom CSS for a better user experience.
- The optimization phase is a placeholder and does not perform actual optimizations.
- The assembly code is simplified and not executable; it’s for visualization only.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

Please ensure your code follows Python PEP 8 standards and test thoroughly.


## Contact
For questions or feedback, feel free to reach out:
- GitHub: [GopalKumar21](https://github.com/GopalKumar21)
- Email: [gopalkumar172111@gmail.com](mailto:gopalkumar172111@gmail.com)
