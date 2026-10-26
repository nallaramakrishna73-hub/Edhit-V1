import crypto from 'crypto';
import { dbManager } from '../database.ts';

export interface KaliAgentInfo {
  agentId: string;
  hostname: string;
  osRelease: string;
  kernel: string;
  ipAddress: string;
  installedTools: string[];
  lastHeartbeat: number;
  status: 'ONLINE' | 'OFFLINE';
}

export interface KaliCommandJob {
  id: string;
  command: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  output: string;
  exitCode?: number;
  createdAt: number;
  completedAt?: number;
}

class KaliBridgeManager {
  private agent: KaliAgentInfo | null = null;
  private commandQueue: KaliCommandJob[] = [];
  private history: KaliCommandJob[] = [];

  constructor() {
    // Check heartbeat expiration every 10 seconds
    setInterval(() => {
      if (this.agent && Date.now() - this.agent.lastHeartbeat > 25000) {
        this.agent.status = 'OFFLINE';
      }
    }, 10000);
  }

  public registerAgent(info: Omit<KaliAgentInfo, 'status' | 'lastHeartbeat'>): KaliAgentInfo {
    this.agent = {
      ...info,
      lastHeartbeat: Date.now(),
      status: 'ONLINE',
    };
    return this.agent;
  }

  public heartbeat(agentId: string): boolean {
    if (this.agent && this.agent.agentId === agentId) {
      this.agent.lastHeartbeat = Date.now();
      this.agent.status = 'ONLINE';
      return true;
    }
    return false;
  }

  public getStatus(): { agent: KaliAgentInfo | null; isConnected: boolean; queueLength: number } {
    const isConnected = Boolean(this.agent && this.agent.status === 'ONLINE');
    return {
      agent: this.agent,
      isConnected,
      queueLength: this.commandQueue.length,
    };
  }

  public queueCommand(command: string): KaliCommandJob {
    const job: KaliCommandJob = {
      id: crypto.randomUUID(),
      command,
      status: 'QUEUED',
      output: '',
      createdAt: Date.now(),
    };

    this.commandQueue.push(job);
    this.history.unshift(job);
    if (this.history.length > 50) this.history.pop();

    return job;
  }

  public getNextCommand(): KaliCommandJob | null {
    const job = this.commandQueue.find((j) => j.status === 'QUEUED');
    if (job) {
      job.status = 'RUNNING';
      return job;
    }
    return null;
  }

  public submitResult(jobId: string, output: string, exitCode: number): boolean {
    const job = this.history.find((j) => j.id === jobId);
    if (job) {
      job.output = output;
      job.exitCode = exitCode;
      job.status = exitCode === 0 ? 'COMPLETED' : 'FAILED';
      job.completedAt = Date.now();

      // Remove from queue
      this.commandQueue = this.commandQueue.filter((j) => j.id !== jobId);
      return true;
    }
    return false;
  }

  public getHistory(): KaliCommandJob[] {
    return this.history;
  }

  public getJob(id: string): KaliCommandJob | undefined {
    return this.history.find((j) => j.id === id);
  }
}

export const kaliBridge = new KaliBridgeManager();
