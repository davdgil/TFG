import { spawn } from 'child_process';
import { NextResponse } from 'next/server';

export async function POST(request) {
  const { tool, args } = await request.json();

  return new Promise((resolve) => {
    const pythonPath = 'C:\\Users\\theivid\\Documents\\GitHub\\TFG\\backend\\venv\\Scripts\\python.exe';
    const scriptPath = 'C:\\Users\\theivid\\Documents\\GitHub\\TFG\\backend\\src\\mcp\\api_bridge.py';

    const process = spawn(pythonPath, [scriptPath, tool, JSON.stringify(args)]);

    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    process.on('close', (code) => {
      if (code !== 0) {
        resolve(NextResponse.json({ error: stderr || 'Error ejecutando tool' }, { status: 500 }));
      } else {
        try {
          const result = JSON.parse(stdout);
          resolve(NextResponse.json({ result }));
        } catch (e) {
          resolve(NextResponse.json({ error: 'Error parsing response', raw: stdout }, { status: 500 }));
        }
      }
    });
  });
}
