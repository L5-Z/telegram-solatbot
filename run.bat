@echo off

REM Step 1: Stop the container (if running)
docker stop solatbot >nul 2>&1
echo Solatbot container stopped successfully

REM Step 2: Remove the container (forcefully)
docker rm -f solatbot >nul 2>&1
echo Solatbot container removed successfully

REM Step 3: Remove the volume manually
docker volume rm solatbot_data >nul 2>&1
echo Solatbot volume removed successfully

REM Step 4: Remove all Docker images
docker rmi -f solatbot >nul 2>&1
echo Solatbot image removed successfully

REM Step 5: Clear Docker build cache
docker builder prune -f >nul 2>&1
echo Solatbot build cache cleared successfully

REM Step 6: Rebuild the Docker image
docker build -t solatbot .
echo Solatbot image rebuilt successfully

REM Step 7: Recreate the volume
docker volume create solatbot_data
echo Solatbot volume recreated successfully

REM Step 8: Create the container with the updated image
docker create --name solatbot --restart always -p 4000:80 -v solatbot_data:/app solatbot
echo Solatbot container created successfully

REM Step 9: Start the container
docker start solatbot
echo Solatbot container started successfully

echo Solatbot update complete!
