<template>
  <div class="home">
    <div class="hero-section">
      <h1 class="hero-title">欢迎使用医疗系统</h1>
      <p class="hero-subtitle">为您提供便捷的医疗服务</p>
    </div>
    
    <div class="features-grid">
      <div class="feature-card" @click="$router.push('/ai-consultation')">
        <div class="feature-icon">🤖</div>
        <h2>AI问诊</h2>
        <p>智能医疗助手，24小时在线为您提供健康咨询和初步诊断建议</p>
        <button class="feature-btn">进入问诊</button>
      </div>
      
      <div class="feature-card" @click="$router.push('/appointment')">
        <div class="feature-icon">📅</div>
        <h2>在线挂号</h2>
        <p>便捷的在线挂号服务，选择科室和医生，轻松预约就诊时间</p>
        <button class="feature-btn">立即挂号</button>
      </div>
      
      <div class="feature-card" @click="$router.push('/navigation-preview')">
        <div class="feature-icon">🗺️</div>
        <h2>院内导航</h2>
        <p>智能院内导航系统，快速找到科室位置，节省您的宝贵时间</p>
        <button class="feature-btn">开始导航</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 3rem 0;
  color: white;
}

.hero-title {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.hero-subtitle {
  font-size: 1.5rem;
  opacity: 0.9;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
}

.feature-card {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
}

.feature-icon {
  font-size: 4rem;
  text-align: center;
  margin-bottom: 1rem;
}

.feature-card h2 {
  color: #667eea;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 1.8rem;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  text-align: center;
}

.feature-btn {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.3s;
}

.feature-btn:hover {
  opacity: 0.9;
}
</style>
