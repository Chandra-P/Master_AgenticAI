# Local braces security fork

This package preserves the MIT-licensed implementation of
[micromatch/braces 3.0.3](https://github.com/micromatch/braces/tree/3.0.3),
including its original LICENSE, with a security fix for
**GHSA-vfj7-8cjw-p6xm**. There is no published patched upstream version.

Changes:

- Limit parser nesting before building overly deep brace/parenthesis ASTs.
- Validate AST depth iteratively before compile, expand, and stringify recurse.
- Apply the limit to direct AST inputs, including cyclic child-node structures.
- Reject excessive nesting with a deliberate `SyntaxError`, rather than a
  call-stack overflow. Callers should handle invalid patterns as usual.

The limit is 128 AST levels and cannot be disabled through options. Ordinary
brace alternatives, ranges, escapes, and glob behavior are retained.

The workspace override replaces the vulnerable registry dependency with this
actual fixed source, rather than suppressing its advisory. Run
`pnpm run test:security` for the regression suite and dependency audit.

When upstream publishes a fix, replace this fork with that release and retain
the regression tests against the replacement.
