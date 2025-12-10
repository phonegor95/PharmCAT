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

#### Unified Script Approach
- **Merged**: `run_pharmcat_online.sh` functionality merged into `run_pharmcat_chinese.sh`
- **Single script**: Now handles both online Docker image and local build
- **Simplified**: One script for all use cases

### 2. **Updated Configuration**

#### `.pharmcat_defaults`
- **Docker image**: `pcat` → `phonegor95/pharmcat:chinese`
- **New settings**: `PHARMCAT_SKIP_PULL`, `PHARMCAT_BUILD_LOCAL`

### 3. **Updated Documentation**

#### `README_Chinese.md`
- **Merged documentation**: Combined with default configuration guide
- **Quick start**: Updated with online image commands
- **Usage examples**: Added online Docker image examples
- **Setup guide**: Comprehensive setup and troubleshooting
- **Configuration**: Added Docker image information

## 🚀 New Usage Options

### **Unified Script Usage**
```bash
# Pull and run (recommended - default behavior)
./run_pharmcat_chinese.sh -i your_file.vcf.gz

# Quick run (skip image update)
./run_pharmcat_chinese.sh --skip-pull -i your_file.vcf.gz

# Force local build
./run_pharmcat_chinese.sh --build-local -i your_file.vcf.gz

# Show image information
./run_pharmcat_chinese.sh --info
```

### **With Aliases (Optional)**
```bash
# Set up aliases (add to ~/.bashrc)
alias pharmcat-cn='./run_pharmcat_chinese.sh'

# Then use:
pharmcat-cn -i your_file.vcf.gz
pharmcat-cn --skip-pull -i your_file.vcf.gz
pharmcat-cn --info
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
1. **Test online image**: `./run_pharmcat_chinese.sh --info`
2. **Run with your data**: `./run_pharmcat_chinese.sh -i your_file.vcf.gz`
3. **Optional**: Set up aliases for convenience

### **For Sharing**
1. **Share Docker image**: `docker pull phonegor95/pharmcat:chinese`
2. **Share repository**: Point users to your GitHub repository
3. **Documentation**: Share `README_Chinese.md`

## 🔧 Troubleshooting

### **If image pull fails**
```bash
# Check Docker Hub connectivity
sudo docker pull hello-world

# Try manual pull
sudo docker pull phonegor95/pharmcat:chinese

# Fallback to local build
./run_pharmcat_chinese.sh --build-local -i your_file.vcf.gz
```

### **To verify setup**
```bash
# Test Chinese translation
./test_chinese_translation.sh

# Show image info
./run_pharmcat_chinese.sh --info

# Check available commands
./run_pharmcat_chinese.sh --help
```

---

**Status**: ✅ **Complete** - PharmCAT Chinese translation now uses online Docker image `phonegor95/pharmcat:chinese`
