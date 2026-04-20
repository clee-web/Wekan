// QR Scanner with jsQR - Camera access and scan detection
class QRScanner {
    constructor() {
        this.video = document.getElementById('qr-video');
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.scanning = false;
        this.currentSessionType = 'class';
        
        this.init();
    }
    
    async init() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            this.video.srcObject = this.stream;
            this.video.onloadedmetadata = () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.startScanning();
            };
        } catch (err) {
            console.error('Camera access denied:', err);
            document.getElementById('result-details').innerHTML = 
                '<div class="alert alert-danger">Camera access required for QR scanning</div>';
        }
        
        // Toggle camera button
document.getElementById('scanner-toggle').onclick = () => this.toggleCamera();
window.startScan = () => {
    scanner.scanning = true;
    scanner.scanLoop();
    document.querySelector('.scanner-container').scrollIntoView({ behavior: 'smooth' });
};
    }
    
    startScanning() {
        this.scanning = true;
        this.scanLoop();
    }
    
    scanLoop() {
        if (!this.scanning) return;
        
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        const code = jsQR(imageData.data, imageData.width, imageData.height);
        if (code) {
            this.processScan(code.data);
            this.scanning = false;  // Pause after successful scan
        }
        
        requestAnimationFrame(() => this.scanLoop());
    }
    
    async processScan(qrData) {
        try {
            console.log('DEBUG: QR data detected:', qrData);
            document.getElementById('scan-result').classList.remove('result-hidden');
            document.getElementById('scan-result').classList.add('result-visible');
            
            const payload = {
                qr_data: qrData,
                session_type: this.currentSessionType
            };
            console.log('DEBUG: Sending payload:', payload);
            
            const response = await fetch('/scan_qr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            console.log('DEBUG: Response status:', response.status);
            const result = await response.json();
            console.log('DEBUG: Response data:', result);
            
            if (result.success) {
                this.showSuccess(result);
                setTimeout(() => {
                    document.getElementById('scan-result').classList.add('result-hidden');
                    this.scanning = true;
                    this.scanLoop();
                }, 5000);
            } else {
                this.showError(result.error || 'Scan failed');
            }
        } catch (err) {
            this.showError('Network error: ' + err.message);
        }
    }
    
    showSuccess(data) {
        const student = data.student;
        const title = document.getElementById('result-title');
        const details = document.getElementById('result-details');
        const countEl = document.getElementById('leadership-count');
        
        title.innerHTML = `<i class="fas fa-check-circle text-success"></i> Attendance Marked!`;
        details.innerHTML = `
            <div class="mb-2">
                <strong>${student.name}</strong><br>
                <small class="text-muted">${student.admission_number} - ${student.class_name}</small>
            </div>
            <span class="badge bg-success fs-6">${data.message}</span>
        `;
        
        // Leadership count if applicable
        if (this.currentSessionType === 'leadership' && student.active === false) {
            countEl.innerHTML = `<i class="fas fa-exclamation-triangle"></i> STUDENT DEACTIVATED - 3+ absences`;
            countEl.classList.add('bg-danger');
        } else {
            countEl.innerHTML = '';
            countEl.classList.remove('bg-danger');
        }
    }
    
    showError(message) {
        document.getElementById('result-title').innerHTML = `<i class="fas fa-times-circle text-danger"></i> Scan Error`;
        document.getElementById('result-details').innerHTML = `<div class="alert alert-danger">${message}</div>`;
        document.getElementById('leadership-count').innerHTML = '';
    }
    
    toggleCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.scanning = false;
        } else {
            this.init();
        }
    }
}

// Global scanner instance
const scanner = new QRScanner();

// Session type handler
function setSessionType(type) {
    scanner.currentSessionType = type;
    document.querySelectorAll('.btn-group button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Visual feedback
    const countEl = document.getElementById('leadership-count');
    if (type === 'leadership') {
        countEl.innerHTML = '<small>Leadership session active</small>';
    } else {
        countEl.innerHTML = '';
    }
}

// Auto-resume scanning after 5s on mobile
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !scanner.scanning) {
        scanner.scanning = true;
        scanner.scanLoop();
    }
});

