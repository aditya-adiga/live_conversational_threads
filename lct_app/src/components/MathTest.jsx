import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default function MathTest() {
  const testMathContent = `
# LaTeX Math Test

## Inline Math
This is an inline equation: $E = mc^2$

## Block Math
Here's a block equation:

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

## More Examples

### Quadratic Formula
$$
x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
$$

### Matrix
$$
\\begin{pmatrix}
a & b \\\\
c & d
\\end{pmatrix}
$$

### Summation
$$
\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\cdots + x_n
$$

### Greek Letters
$\\alpha, \\beta, \\gamma, \\delta, \\epsilon, \\theta, \\lambda, \\mu, \\pi, \\sigma, \\phi, \\psi, \\omega$

### Subscripts and Superscripts
$f(x) = x^2 + 2x + 1$ and $a_{ij} = b_i^j$

### Fractions and Roots
$\\frac{a}{b}$ and $\\sqrt{x}$ and $\\sqrt[3]{x}$

### Integrals and Derivatives
$\\int f(x) dx$ and $\\frac{d}{dx}f(x)$ and $\\frac{\\partial f}{\\partial x}$
`;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
        LaTeX Math Rendering Test
      </h1>
      
      <div className="prose prose-lg max-w-none text-gray-800 leading-relaxed">
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {testMathContent}
        </ReactMarkdown>
      </div>
      
      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">Test Instructions:</h3>
        <ul className="text-blue-700 space-y-1">
          <li>• If you see properly formatted math equations above, LaTeX rendering is working!</li>
          <li>• Inline math should appear inline with text (e.g., E = mc²)</li>
          <li>• Block math should appear centered on separate lines</li>
          <li>• If you see raw LaTeX code (like $E = mc^2$), rendering is not working</li>
        </ul>
      </div>
    </div>
  );
}
