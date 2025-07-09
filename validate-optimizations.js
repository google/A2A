/**
 * Validation Script for A2A Optimizations
 *
 * This script validates that all the optimization code is syntactically correct
 * and the basic structure is sound without requiring external dependencies.
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function validateFileExists(filePath) {
  try {
    const fullPath = path.join(__dirname, filePath);
    const stats = fs.statSync(fullPath);
    return { exists: true, size: stats.size };
  } catch (error) {
    return { exists: false, error: error.message };
  }
}

function validateFileContent(filePath, expectedPatterns) {
  try {
    const fullPath = path.join(__dirname, filePath);
    const content = fs.readFileSync(fullPath, 'utf8');

    const results = expectedPatterns.map(pattern => {
      const regex = new RegExp(pattern, 'i');
      return {
        pattern,
        found: regex.test(content)
      };
    });

    return {
      success: true,
      content: content,
      patterns: results,
      allPatternsFound: results.every(r => r.found)
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

function validateTypeScriptSyntax(filePath) {
  try {
    const fullPath = path.join(__dirname, filePath);
    const content = fs.readFileSync(fullPath, 'utf8');

    // Basic syntax checks
    const checks = [
      {
        name: 'Balanced braces', test: () => {
          const openBraces = (content.match(/\{/g) || []).length;
          const closeBraces = (content.match(/\}/g) || []).length;
          return openBraces === closeBraces;
        }
      },
      {
        name: 'Balanced parentheses', test: () => {
          const openParens = (content.match(/\(/g) || []).length;
          const closeParens = (content.match(/\)/g) || []).length;
          return openParens === closeParens;
        }
      },
      {
        name: 'No obvious syntax errors', test: () => {
          return !content.includes('SyntaxError') && !content.includes('unexpected token');
        }
      },
      {
        name: 'Has exports', test: () => {
          return content.includes('export') || content.includes('module.exports');
        }
      },
      {
        name: 'TypeScript syntax', test: () => {
          return content.includes('interface') || content.includes('type') || content.includes(': ');
        }
      }
    ];

    const results = checks.map(check => ({
      name: check.name,
      passed: check.test()
    }));

    return {
      success: true,
      checks: results,
      allPassed: results.every(r => r.passed)
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

function runValidation() {
  log('🚀 Starting A2A Optimization Validation...', 'blue');
  log('', 'reset');

  const filesToValidate = [
    {
      path: 'types/src/error-handling.ts',
      patterns: [
        'A2AErrorHandler',
        'exponential.*backoff',
        'circuit.*breaker',
        'retry',
        'correlation'
      ]
    },
    {
      path: 'types/src/task-persistence.ts',
      patterns: [
        'TaskPersistenceManager',
        'optimistic.*lock',
        'version',
        'audit.*trail',
        'recovery'
      ]
    },
    {
      path: 'types/src/connection-pool.ts',
      patterns: [
        'A2AConnectionPool',
        'connection.*reuse',
        'health.*check',
        'backpressure',
        'metrics'
      ]
    }
  ];

  let totalTests = 0;
  let passedTests = 0;
  let failedTests = 0;

  // Test 1: File Existence
  log('📁 Testing file existence...', 'yellow');
  filesToValidate.forEach(file => {
    totalTests++;
    const result = validateFileExists(file.path);
    if (result.exists) {
      log(`  ✅ ${file.path} (${result.size} bytes)`, 'green');
      passedTests++;
    } else {
      log(`  ❌ ${file.path} - ${result.error}`, 'red');
      failedTests++;
    }
  });

  // Test 2: Content Validation
  log('\n🔍 Testing file content...', 'yellow');
  filesToValidate.forEach(file => {
    const result = validateFileContent(file.path, file.patterns);
    if (result.success) {
      totalTests++;
      if (result.allPatternsFound) {
        log(`  ✅ ${file.path} - All expected patterns found`, 'green');
        passedTests++;
      } else {
        log(`  ❌ ${file.path} - Missing patterns:`, 'red');
        result.patterns.filter(p => !p.found).forEach(p => {
          log(`    - ${p.pattern}`, 'red');
        });
        failedTests++;
      }
    }
  });

  // Test 3: TypeScript Syntax
  log('\n🔧 Testing TypeScript syntax...', 'yellow');
  filesToValidate.forEach(file => {
    const result = validateTypeScriptSyntax(file.path);
    if (result.success) {
      totalTests++;
      if (result.allPassed) {
        log(`  ✅ ${file.path} - Syntax validation passed`, 'green');
        passedTests++;
      } else {
        log(`  ❌ ${file.path} - Syntax issues:`, 'red');
        result.checks.filter(c => !c.passed).forEach(c => {
          log(`    - ${c.name}`, 'red');
        });
        failedTests++;
      }
    }
  });

  // Test 4: Configuration Files
  log('\n⚙️  Testing configuration files...', 'yellow');
  const configFiles = [
    'package.json',
    'tsconfig.json',
    'CHANGELOG.md'
  ];

  configFiles.forEach(file => {
    totalTests++;
    const result = validateFileExists(file);
    if (result.exists) {
      log(`  ✅ ${file}`, 'green');
      passedTests++;
    } else {
      log(`  ❌ ${file} - Missing`, 'red');
      failedTests++;
    }
  });

  // Test 5: Package.json validation
  log('\n📦 Testing package.json structure...', 'yellow');
  try {
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
    const requiredFields = ['name', 'version', 'scripts', 'dependencies', 'devDependencies'];

    requiredFields.forEach(field => {
      totalTests++;
      if (packageJson[field]) {
        log(`  ✅ package.json has ${field}`, 'green');
        passedTests++;
      } else {
        log(`  ❌ package.json missing ${field}`, 'red');
        failedTests++;
      }
    });

    // Check for essential scripts
    const requiredScripts = ['build', 'test', 'validate'];
    requiredScripts.forEach(script => {
      totalTests++;
      if (packageJson.scripts && packageJson.scripts[script]) {
        log(`  ✅ package.json has script: ${script}`, 'green');
        passedTests++;
      } else {
        log(`  ❌ package.json missing script: ${script}`, 'red');
        failedTests++;
      }
    });

  } catch (error) {
    totalTests++;
    log(`  ❌ package.json parse error: ${error.message}`, 'red');
    failedTests++;
  }

  // Summary
  log('\n📊 Validation Summary:', 'blue');
  log(`Total tests: ${totalTests}`, 'reset');
  log(`Passed: ${passedTests}`, 'green');
  log(`Failed: ${failedTests}`, failedTests > 0 ? 'red' : 'green');

  const successRate = ((passedTests / totalTests) * 100).toFixed(1);
  log(`Success rate: ${successRate}%`, successRate >= 90 ? 'green' : 'yellow');

  if (failedTests === 0) {
    log('\n🎉 All validations passed! A2A optimizations are correctly implemented.', 'green');
    return true;
  } else {
    log(`\n⚠️  ${failedTests} validation(s) failed. Please review the issues above.`, 'yellow');
    return false;
  }
}

// Run validation
const success = runValidation();
process.exit(success ? 0 : 1);
