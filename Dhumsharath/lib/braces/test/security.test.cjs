'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const path = require('node:path');
const braces = require('..');

const nestingError = { name: 'SyntaxError', message: /nesting limit/ };
// Both payloads stay below upstream's 10,000-character limit.
const deepBrace = '{'.repeat(4500) + 'a,b' + '}'.repeat(4500);
const deepParen = '('.repeat(4500) + 'a' + ')'.repeat(4500);

test('ordinary alternatives, numeric ranges, nested braces, and escapes work', () => {
  assert.deepEqual(braces.expand('src/{a,b}.js'), ['src/a.js', 'src/b.js']);
  assert.deepEqual(braces.expand('{1..3}'), ['1', '2', '3']);
  assert.deepEqual(braces.expand('{a,{b,c}}'), ['a', 'b', 'c']);
  assert.deepEqual(braces.expand(String.raw`x/\{a,b\}`), ['x/{a,b}']);
  assert.equal(braces.compile('src/{a,b}.js'), 'src/(a|b).js');
  assert.equal(braces.stringify(braces.parse('src/{a,b}.js')), 'src/{a,b}.js');
  assert.deepEqual(braces(['{a,b}', '{b,c}'], { expand: true, nodupes: true }), ['a', 'b', 'c']);
});

test('all string entry points reject the reported deeply nested brace input', () => {
  for (const fn of [braces, braces.create, braces.parse, braces.compile, braces.expand, braces.stringify]) {
    assert.throws(() => fn(deepBrace), nestingError);
  }
});

test('parentheses and unbalanced braces cannot bypass the nesting limit', () => {
  assert.throws(() => braces.parse(deepParen), nestingError);
  assert.throws(() => braces.parse('{'.repeat(10000)), nestingError);
  assert.throws(() => braces.parse(deepBrace, { maxDepth: Infinity, maxLength: Infinity }), nestingError);
  assert.throws(() => braces([deepBrace]), nestingError);
});

test('moderately nested patterns below the limit remain supported', () => {
  const pattern = '{'.repeat(20) + 'a,b' + '}'.repeat(20);
  assert.deepEqual(braces.expand(pattern), [
    '{'.repeat(19) + 'a' + '}'.repeat(19),
    '{'.repeat(19) + 'b' + '}'.repeat(19),
  ]);
  assert.equal(braces.stringify(braces.parse(pattern)), pattern);
});

test('recursive AST entry points reject deep or cyclic child structures', () => {
  let ast = { type: 'text', value: 'a' };
  for (let n = 0; n < 10000; n++) ast = { type: 'root', nodes: [ast] };
  for (const fn of [braces.compile, braces.expand, braces.stringify]) {
    assert.throws(() => fn(ast), nestingError);
  }
  const cyclic = { type: 'root', nodes: [] };
  cyclic.nodes.push(cyclic);
  for (const fn of [braces.compile, braces.expand, braces.stringify]) {
    assert.throws(() => fn(cyclic), nestingError);
  }
});

test('HTTP proxy micromatch resolves the fixed fork and retains glob matching', () => {
  const serverDir = path.resolve(__dirname, '../../../artifacts/api-server');
  const proxyRequire = createRequire(require.resolve('http-proxy-middleware', { paths: [serverDir] }));
  const micromatchFile = proxyRequire.resolve('micromatch');
  const micromatchRequire = createRequire(micromatchFile);
  assert.equal(micromatchRequire('braces'), braces);
  const micromatch = proxyRequire('micromatch');
  assert.deepEqual(micromatch.braceExpand('src/{a,b}.js'), ['src/a.js', 'src/b.js']);
  assert.equal(micromatch.isMatch('src/a.js', 'src/{a,b}.js'), true);
  assert.equal(micromatch.isMatch('src/c.js', 'src/{a,b}.js'), false);
  assert.throws(() => micromatch.braceExpand(deepBrace), nestingError);
});
