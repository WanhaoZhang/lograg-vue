const mongoose = require('mongoose');

async function clearDatabase() {
  try {
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/loganalysis';
    console.log(`正在连接到MongoDB: ${mongoUri}`);
    
    await mongoose.connect(mongoUri);
    console.log('已连接到MongoDB');
    
    // 获取所有集合名称
    const collections = await mongoose.connection.db.collections();
    
    // 清空每个集合
    for (let collection of collections) {
      await collection.deleteMany({});
      console.log(`已清空集合: ${collection.collectionName}`);
    }
    
    console.log('所有集合已清空');
    await mongoose.disconnect();
    console.log('已断开MongoDB连接');
    
    process.exit(0);
  } catch (error) {
    console.error('清空数据库失败:', error);
    process.exit(1);
  }
}

clearDatabase(); 