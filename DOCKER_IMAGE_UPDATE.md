# PharmCAT Chinese Translation - Docker Image Update

## 🎯 Summary

Successfully updated PharmCAT Chinese translation to use the online Docker image `phonegor95/pharmcat:chinese` that you pushed to Docker Hub.

## 📋 Changes Made

### 1. **Updated Scripts**

#### `run_pharmcat_chinese.sh`
- **Changed Docker image**: `pcat` → `phonegor95/pharmcat:chinese`
- **Added pull functionality**: New `pull_docker()` function
- **Updated command options**:
  - `--skip-build` → `--skip-pull` (legacy support maintained)
  - Added `--build-local` for local building
- **Default behavior**: Now pulls from Docker Hub instead of building locally

#### `run_pharmcat_online.sh` (NEW)
- **Purpose**: Dedicated script for using online Docker image
- **Features**: 
  - Automatic image pulling
  - Image information display
  - Streamlined online-only workflow
- **Usage**: `./run_pharmcat_online.sh -i your_file.vcf.gz`

### 2. **Updated Configuration**

#### `.pharmcat_defaults`
- **Docker image**: `pcat` → `phonegor95/pharmcat:chinese`
- **New settings**: `PHARMCAT_SKIP_PULL`, `PHARMCAT_BUILD_LOCAL`

#### `pharmcat_chinese_default.sh`
- **New aliases**:
  - `pharmcat-online` → Online Docker image runner
  - `pharmcat-quick` → Quick run without image update
  - `pharmcat-build-cn` → Local build (updated)
- **Environment variables**: Added `PHARMCAT_DOCKER_IMAGE`

### 3. **Updated Documentation**

#### `README_Chinese_Default.md`
- **Quick start**: Updated with online image commands
- **Usage examples**: Added online Docker image examples
- **Command aliases**: Updated with new aliases
- **Configuration**: Added Docker image information

## 🚀 New Usage Options

### **Recommended: Online Docker Image**
```bash
# Pull and run (recommended for first time)
pharmcat-online -i your_file.vcf.gz

# Quick run (skip image update)
pharmcat-quick -i your_file.vcf.gz

# Show image information
pharmcat-online --info
```

### **Traditional: Auto Pull/Build**
```bash
# Automatically pull from Docker Hub
pharmcat-cn -i your_file.vcf.gz

# Use existing image (no pull/build)
pharmcat-cn --skip-pull -i your_file.vcf.gz

# Force local build
pharmcat-cn --build-local -i your_file.vcf.gz
```

### **Direct Docker Commands**
```bash
# Pull the image
sudo docker pull phonegor95/pharmcat:chinese

# Run directly
sudo docker run --rm -v $(pwd):/pharmcat/data phonegor95/pharmcat:chinese pharmcat_pipeline "data/your_file.vcf.gz" --missing-to-ref -G -reporterHtml -reporterJson
```

## 📊 Benefits of Online Docker Image

### ✅ **Advantages**
1. **No local build required** - Saves time and resources
2. **Consistent environment** - Same image for all users
3. **Easy sharing** - Others can use `docker pull phonegor95/pharmcat:chinese`
4. **Automatic updates** - Pull latest version when needed
5. **Reduced storage** - No need to store build artifacts locally

### 🔄 **Backward Compatibility**
- All existing commands still work
- `--skip-build` option maintained for compatibility
- Local building still available with `--build-local`

## 🌐 Docker Hub Information

- **Repository**: `phonegor95/pharmcat`
- **Tag**: `chinese`
- **Size**: 3.91GB
- **Features**: Complete Chinese translation support
- **URL**: https://hub.docker.com/r/phonegor95/pharmcat

## 📝 Next Steps

### **For Users**
1. **Update aliases**: Run `source ~/.bashrc`
2. **Test online image**: `pharmcat-online --info`
3. **Run with your data**: `pharmcat-online -i your_file.vcf.gz`

### **For Sharing**
1. **Share Docker image**: `docker pull phonegor95/pharmcat:chinese`
2. **Share repository**: Point users to your GitHub repository
3. **Documentation**: Share `README_Chinese_Default.md`

## 🔧 Troubleshooting

### **If image pull fails**
```bash
# Check Docker Hub connectivity
sudo docker pull hello-world

# Try manual pull
sudo docker pull phonegor95/pharmcat:chinese

# Fallback to local build
pharmcat-cn --build-local -i your_file.vcf.gz
```

### **If aliases don't work**
```bash
# Reload bash configuration
source ~/.bashrc

# Or run setup script again
./pharmcat_chinese_default.sh
```

### **To verify setup**
```bash
# Test Chinese translation
pharmcat-test-cn

# Show image info
pharmcat-online --info

# Check available commands
pharmcat-online --help
```

---

**Status**: ✅ **Complete** - PharmCAT Chinese translation now uses online Docker image `phonegor95/pharmcat:chinese`
