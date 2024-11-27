class PDFViewer {
    constructor(container, pdfUrl) {
        this.container = container;
        this.pdfUrl = pdfUrl;
        this.currentPage = 1;
        this.pageCount = 0;
        this.chapters = [];
        this.loadLastPosition();
        this.init();
    }

    async init() {
        const loadingTask = pdfjsLib.getDocument(this.pdfUrl);
        this.pdf = await loadingTask.promise;
        this.pageCount = this.pdf.numPages;
        
        await this.setupViewer();
        await this.extractChapters();
        this.setupControls();
        this.goToPage(this.currentPage);
    }

    async setupViewer() {
        const controls = document.createElement('div');
        controls.className = 'pdf-controls';
        controls.innerHTML = `
            <div class="pdf-navigation">
                <button class="btn btn-icon" id="prevPage">◀</button>
                <span class="page-info">
                    Page <input type="number" id="currentPage" value="1" min="1"> 
                    of <span id="pageCount">0</span>
                </span>
                <button class="btn btn-icon" id="nextPage">▶</button>
            </div>
            <div class="pdf-chapters">
                <select id="chapterSelect">
                    <option value="">Jump to Chapter...</option>
                </select>
            </div>
        `;
        this.container.prepend(controls);
    }

    async extractChapters() {
        // Simple chapter detection based on text size and position
        for (let i = 1; i <= this.pageCount; i++) {
            const page = await this.pdf.getPage(i);
            const textContent = await page.getTextContent();
            
            for (const item of textContent.items) {
                if (item.height > 14 && item.str.toLowerCase().includes('chapter')) {
                    this.chapters.push({
                        title: item.str,
                        page: i
                    });
                }
            }
        }

        // Populate chapters dropdown
        const select = document.getElementById('chapterSelect');
        this.chapters.forEach(chapter => {
            const option = document.createElement('option');
            option.value = chapter.page;
            option.textContent = chapter.title;
            select.appendChild(option);
        });
    }

    setupControls() {
        document.getElementById('prevPage').onclick = () => this.prevPage();
        document.getElementById('nextPage').onclick = () => this.nextPage();
        document.getElementById('currentPage').onchange = (e) => {
            this.goToPage(parseInt(e.target.value));
        };
        document.getElementById('chapterSelect').onchange = (e) => {
            if (e.target.value) {
                this.goToPage(parseInt(e.target.value));
            }
        };

        // Save position periodically
        setInterval(() => this.savePosition(), 5000);
    }

    async goToPage(pageNumber) {
        if (pageNumber < 1 || pageNumber > this.pageCount) return;
        
        this.currentPage = pageNumber;
        const page = await this.pdf.getPage(pageNumber);
        const viewport = page.getViewport({ scale: 1.5 });
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        const viewer = document.getElementById('pdfViewer');
        viewer.innerHTML = '';
        viewer.appendChild(canvas);
        
        document.getElementById('currentPage').value = pageNumber;
        document.getElementById('pageCount').textContent = this.pageCount;
        
        this.savePosition();
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.goToPage(this.currentPage - 1);
        }
    }

    nextPage() {
        if (this.currentPage < this.pageCount) {
            this.goToPage(this.currentPage + 1);
        }
    }

    savePosition() {
        const key = `pdf_position_${this.pdfUrl}`;
        localStorage.setItem(key, this.currentPage);
    }

    loadLastPosition() {
        const key = `pdf_position_${this.pdfUrl}`;
        const savedPage = localStorage.getItem(key);
        if (savedPage) {
            this.currentPage = parseInt(savedPage);
        }
    }
} 