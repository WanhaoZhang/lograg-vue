FROM node:18-alpine

WORKDIR /app

# 安装 cnpm
RUN npm install -g cnpm --registry=https://registry.npmmirror.com

COPY package*.json ./

# 使用 cnpm 安装依赖
RUN cnpm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"] 