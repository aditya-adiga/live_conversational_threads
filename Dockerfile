# --------- Frontend Build Stage ---------
    FROM node:18 AS frontend-builder

    WORKDIR /app/lct_app
    
    # Copy frontend source code
    COPY lct_app/ ./
    
    # Install deps and build
    RUN npm install && npm run build
    
    # Debug: Print frontend dist contents
    RUN echo "Contents of dist folder:" && ls -l dist && echo "Contents of dist/assets:" && ls -l dist/assets
    
    
    # --------- Backend Final Stage ---------
    FROM python:3.11-slim
    
    WORKDIR /app
    
    # Install dependencies
    COPY lct_python_backend/requirements.txt ./requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copy backend code
    COPY lct_python_backend/ ./lct_python_backend/
    
    # Copy built frontend from previous stage
    COPY --from=frontend-builder /app/lct_app/dist/ ./frontend_dist/
    
    # Debug: Confirm frontend_dist structure
    RUN echo "Final frontend_dist contents:" && ls -l frontend_dist && echo "frontend_dist/assets:" && ls -l frontend_dist/assets
    
    # Set runtime port
    ENV PORT=8080
    
    # Expose port
    EXPOSE 8080
    
    # Start FastAPI app
    CMD ["uvicorn", "lct_python_backend.backend:lct_app", "--host", "0.0.0.0", "--port", "8080"]