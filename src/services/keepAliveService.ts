// services/keepAliveService.ts

class KeepAliveService {
    private pingInterval: NodeJS.Timeout | null = null;
    private API_URL: string = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    private PING_INTERVAL: number = 14 * 60 * 1000; // 14 minutes (Render free tier sleeps after 15)
    private isActive: boolean = false;
  
    constructor() {
      // Start keep-alive when the service is created
      this.start();
      
      // Handle page visibility changes
      this.setupVisibilityHandlers();
    }
  
    start() {
      if (this.isActive) return;
      
      console.log('🔄 Starting keep-alive service...');
      this.isActive = true;
      
      // Send initial ping
      this.ping();
      
      // Set up regular pings
      this.pingInterval = setInterval(() => {
        this.ping();
      }, this.PING_INTERVAL);
    }
  
    stop() {
      if (!this.isActive) return;
      
      console.log('⏹️ Stopping keep-alive service...');
      this.isActive = false;
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
    }
  
    private async ping() {
      try {
        const startTime = Date.now();
        const response = await fetch(`${this.API_URL}/keep-alive`, {
          method: 'GET',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
          console.log(`✅ Keep-alive ping successful (${responseTime}ms)`);
        } else {
          console.warn(`⚠️ Keep-alive ping failed with status: ${response.status}`);
        }
      } catch (error) {
        console.warn('❌ Keep-alive ping failed:', error);
        // Don't throw - just log the failure
      }
    }
  
    private setupVisibilityHandlers() {
      // Stop pinging when page is hidden to save resources
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          console.log('📱 Page hidden - continuing keep-alive in background');
          // Keep running to maintain server warmth
        } else {
          console.log('👀 Page visible - ensuring keep-alive is active');
          if (!this.isActive) {
            this.start();
          }
        }
      });
  
      // Handle page unload
      window.addEventListener('beforeunload', () => {
        // Don't stop keep-alive on unload - other tabs might still need it
        console.log('🚪 Page unloading - keep-alive continues for other tabs');
      });
    }
  
    // Manual health check method
    async checkServerHealth(): Promise<{
      status: 'healthy' | 'unhealthy' | 'cold_start';
      responseTime: number;
    }> {
      try {
        const startTime = Date.now();
        const response = await fetch(`${this.API_URL}/health`, {
          method: 'GET',
          mode: 'cors'
        });
        
        const responseTime = Date.now() - startTime;
        
        if (response.ok) {
          const data = await response.json();
          return {
            status: 'healthy',
            responseTime
          };
        } else {
          return {
            status: 'unhealthy',
            responseTime
          };
        }
      } catch (error) {
        // If request takes a long time or fails, likely a cold start
        return {
          status: 'cold_start',
          responseTime: -1
        };
      }
    }
  
    // Get service status
    getStatus() {
      return {
        isActive: this.isActive,
        pingInterval: this.PING_INTERVAL,
        nextPingIn: this.pingInterval ? this.PING_INTERVAL : null
      };
    }
  }
  
  // Create singleton instance
  const keepAliveService = new KeepAliveService();
  
  // Export for manual control if needed
  export default keepAliveService;
  
  // Also export the class for testing
  export { KeepAliveService };