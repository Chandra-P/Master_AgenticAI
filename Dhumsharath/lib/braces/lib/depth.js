'use strict';

const MAX_DEPTH = 128;
const nestingError = () => new SyntaxError(`Brace AST exceeds nesting limit (${MAX_DEPTH})`);

// Do not follow parent/prev links: normal brace ASTs contain those back-links.
// Iteration ensures even a hostile or cyclic child AST cannot overflow the stack.
const assertSafeAst = ast => {
  const stack = [{ node: ast, depth: 0 }];
  while (stack.length > 0) {
    const { node, depth } = stack.pop();
    if (depth > MAX_DEPTH) throw nestingError();
    if (node && Array.isArray(node.nodes)) {
      for (const child of node.nodes) {
        stack.push({ node: child, depth: depth + 1 });
      }
    }
  }
};

module.exports = { MAX_DEPTH, nestingError, assertSafeAst };
