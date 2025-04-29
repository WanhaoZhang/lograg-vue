FROM node:18-alpine

WORKDIR /app

# 安装 cnpm
RUN npm install -g cnpm --registry=https://registry.npmmirror.com

COPY package*.json ./

# 使用 cnpm 安装依赖
RUN cnpm install

COPY . .

EXPOSE 8080

ENV HOST=0.0.0.0
ENV PORT=8080

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"] 