#!/usr/bin/env node

const { execSync } = require('child_process');
const readline = require('readline');

const PORTS = [3000, 8000];
const isWindows = process.platform === 'win32';

// ANSI 색상 코드
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function getProcessesOnPort(port) {
  try {
    let output;
    if (isWindows) {
      output = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf-8' });
    } else {
      output = execSync(`lsof -i :${port} -t`, { encoding: 'utf-8' });
    }

    if (!output || output.trim() === '') {
      return [];
    }

    if (isWindows) {
      // Windows에서 LISTENING 상태의 PID만 추출
      const lines = output.split('\n').filter(line => line.includes('LISTENING'));
      const pids = [...new Set(lines.map(line => {
        const parts = line.trim().split(/\s+/);
        return parts[parts.length - 1];
      }).filter(pid => pid && pid !== '0'))];
      return pids;
    } else {
      // Unix/Mac에서 PID 추출
      return output.trim().split('\n').filter(pid => pid);
    }
  } catch (error) {
    return [];
  }
}

function killProcess(pid) {
  try {
    if (isWindows) {
      // Windows: 프로세스 트리 전체를 종료
      execSync(`taskkill /F /T /PID ${pid}`, { stdio: 'ignore' });
    } else {
      execSync(`kill -9 ${pid}`, { stdio: 'ignore' });
    }
    return true;
  } catch (error) {
    // 프로세스가 이미 종료되었을 수 있음 - 재확인
    return !isProcessRunning(pid);
  }
}

function isProcessRunning(pid) {
  try {
    if (isWindows) {
      execSync(`tasklist /FI "PID eq ${pid}"`, { encoding: 'utf-8' });
      return true;
    } else {
      execSync(`ps -p ${pid}`, { stdio: 'ignore' });
      return true;
    }
  } catch (error) {
    return false;
  }
}

function killProcessesByName(processName) {
  try {
    if (isWindows) {
      execSync(`taskkill /F /IM ${processName}`, { stdio: 'ignore' });
    } else {
      execSync(`pkill -9 ${processName}`, { stdio: 'ignore' });
    }
    return true;
  } catch (error) {
    return false;
  }
}

function askQuestion(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.toLowerCase());
    });
  });
}

async function main() {
  log('\n🔍 포트 사용 현황을 확인하는 중...\n', 'cyan');

  const portsInUse = [];

  for (const port of PORTS) {
    const pids = getProcessesOnPort(port);
    if (pids.length > 0) {
      portsInUse.push({ port, pids });
      log(`⚠️  포트 ${port}이(가) 사용 중입니다 (PID: ${pids.join(', ')})`, 'yellow');
    } else {
      log(`✅ 포트 ${port}은(는) 사용 가능합니다`, 'green');
    }
  }

  if (portsInUse.length === 0) {
    log('\n✨ 모든 포트가 사용 가능합니다. 서버를 시작합니다...\n', 'green');
    return;
  }

  log('\n📋 다음 포트들이 사용 중입니다:', 'yellow');
  portsInUse.forEach(({ port, pids }) => {
    log(`   - 포트 ${port}: PID ${pids.join(', ')}`, 'yellow');
  });

  const answer = await askQuestion('\n❓ 사용 중인 프로세스를 종료하고 새로 시작하시겠습니까? (y/n): ');

  if (answer === 'y' || answer === 'yes') {
    log('\n🔄 프로세스를 종료하는 중...\n', 'cyan');

    let allKilled = true;
    const failedPids = [];

    for (const { port, pids } of portsInUse) {
      for (const pid of pids) {
        if (killProcess(pid)) {
          log(`✅ PID ${pid} (포트 ${port}) 종료 완료`, 'green');
        } else {
          log(`⚠️  PID ${pid} (포트 ${port}) 종료 실패 - 재시도 중...`, 'yellow');
          failedPids.push({ pid, port });
        }
      }
    }

    // 실패한 프로세스 재시도
    if (failedPids.length > 0) {
      log('\n🔄 Python 프로세스를 강제 종료하는 중...\n', 'cyan');

      if (isWindows) {
        // Windows에서 python.exe와 node.exe 프로세스 종료
        killProcessesByName('python.exe');
        killProcessesByName('python3.exe');

        // 잠시 대기
        execSync('timeout /t 2 /nobreak', { stdio: 'ignore' });
      } else {
        killProcessesByName('python');
        killProcessesByName('python3');
        killProcessesByName('node');
      }

      // 포트가 실제로 비었는지 확인
      for (const { port } of failedPids) {
        const remainingPids = getProcessesOnPort(port);
        if (remainingPids.length === 0) {
          log(`✅ 포트 ${port} 정리 완료`, 'green');
        } else {
          log(`❌ 포트 ${port} 여전히 사용 중 (PID: ${remainingPids.join(', ')})`, 'red');
          allKilled = false;
        }
      }
    }

    if (allKilled || failedPids.length === 0) {
      log('\n✨ 모든 포트가 정리되었습니다. 서버를 시작합니다...\n', 'green');
    } else {
      log('\n⚠️  일부 포트 정리에 실패했습니다. 수동으로 종료 후 다시 시도해주세요.\n', 'yellow');
      log('💡 Tip: 작업 관리자를 열어서 python.exe 프로세스를 직접 종료해보세요.\n', 'cyan');
      process.exit(1);
    }
  } else {
    log('\n❌ 사용자가 취소했습니다. 서버를 시작하지 않습니다.\n', 'red');
    process.exit(1);
  }
}

main().catch(error => {
  log(`\n❌ 오류 발생: ${error.message}\n`, 'red');
  process.exit(1);
});
