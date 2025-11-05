#!/bin/bash

# CodeArtifact 配置脚本
# 用于配置 Poetry 使用 AWS CodeArtifact 私有仓库
# package部署于AWS Codeartifact私有仓库, 需要配置AWS凭证才能安装, 并设置AWS_PROFILE环境变量, 推荐使用SSO登录
#  1. 安装AWS CLI
#  2. 管理员帮你开通AWS的账号
#  3. 执行 `aws configure sso --profile oxsci-dev` 配置AWS凭证,根据提示输入以下配置
#     - SSO session name (Recommended): oxsci-dev
#     - SSO start URL: https://oxsci-ai.awsapps.com/start
#     - SSO region: ap-southeast-1
#     - SSO registration scopes: sso:account:access
#  4. 然后就会跳出登录页面进行登录
#  5. 登录成功后,选择默认region 为 ap-southeast-1, 并选择默认output 为 json
#  6. copy script下的 `entrypoint-dev.sh` 到项目根目录下, 并执行 `chmod +x entrypoint-dev.sh`
#  7. 在项目根目录下执行 `./entrypoint-dev.sh` 即可 (每12小时需要执行一次)

set -e # 遇到错误立即退出

PROFILE="oxsci-dev"
DOMAIN="oxsci-domain"
DOMAIN_OWNER="000373574646"
REPOSITORY="oxsci-pypi"
REGION="ap-southeast-1"

echo "🔧 开始配置 AWS CodeArtifact 用于 Poetry..."

# 检查 AWS CLI 是否安装
if ! command -v aws &>/dev/null; then
    echo "❌ AWS CLI 未安装，请先安装 AWS CLI"
    exit 1
fi

# 检查 Poetry 是否安装
if ! command -v poetry &>/dev/null; then
    echo "❌ Poetry 未安装，请先安装 Poetry"
    exit 1
fi

# 检查 AWS Profile 是否存在
echo "🔍 检查 AWS Profile: $PROFILE"
if ! aws configure list-profiles | grep -q "^$PROFILE$"; then
    echo "❌ AWS Profile '$PROFILE' 不存在"
    echo ""
    echo "请配置 AWS Profile，推荐使用 SSO："
    echo "  aws configure sso --profile $PROFILE"
    echo ""
    echo "或者使用传统方式配置："
    echo "  aws configure --profile $PROFILE"
    echo ""
    echo "确保 Profile 具有 CodeArtifact 相关权限："
    echo "  - codeartifact:GetRepositoryEndpoint"
    echo "  - codeartifact:GetAuthorizationToken"
    exit 1
fi

# 测试 Profile 是否有效，如果无效则尝试自动登录
echo "🔐 验证 AWS Profile 权限..."
if ! aws sts get-caller-identity --profile $PROFILE >/dev/null 2>&1; then
    echo "⚠️  AWS Profile '$PROFILE' 无法验证身份，尝试自动登录..."
    if aws sso login --profile $PROFILE; then
        echo "✅ SSO 登录成功"
    else
        echo "❌ SSO 登录失败，请手动执行："
        echo "  aws sso login --profile $PROFILE"
        exit 1
    fi
else
    echo "✅ AWS Profile 验证成功"
fi

# 获取 CodeArtifact 仓库 URL
echo "🌐 获取 CodeArtifact 仓库端点..."
REPO_URL=$(aws codeartifact get-repository-endpoint \
    --profile $PROFILE \
    --domain $DOMAIN \
    --domain-owner $DOMAIN_OWNER \
    --repository $REPOSITORY \
    --format pypi \
    --region $REGION \
    --query repositoryEndpoint --output text)

if [ $? -ne 0 ] || [ -z "$REPO_URL" ]; then
    echo "❌ 获取仓库端点失败，请检查权限和参数"
    exit 1
fi

echo "✅ 仓库端点获取成功: $REPO_URL"

# 配置 Poetry 仓库
echo "📦 配置 Poetry 仓库..."
poetry config repositories.oxsci-ca ${REPO_URL}

if [ $? -ne 0 ]; then
    echo "❌ Poetry 仓库配置失败"
    exit 1
fi

echo "✅ Poetry 仓库配置成功"

# 获取认证令牌
echo "🔑 获取认证令牌..."
AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --profile $PROFILE \
    --domain $DOMAIN \
    --domain-owner $DOMAIN_OWNER \
    --region $REGION \
    --query authorizationToken \
    --output text)

if [ $? -ne 0 ] || [ -z "$AUTH_TOKEN" ]; then
    echo "❌ 获取认证令牌失败"
    exit 1
fi

echo "✅ 认证令牌获取成功"

# 配置 Poetry 认证
echo "🔐 配置 Poetry 认证..."
poetry config http-basic.oxsci-ca aws ${AUTH_TOKEN}

if [ $? -ne 0 ]; then
    echo "❌ Poetry 认证配置失败"
    exit 1
fi

echo "✅ Poetry 认证配置成功"

echo ""
echo "🎉 CodeArtifact 配置完成！"
echo "📋 配置信息："
echo "  - 仓库名称: oxsci-ca"
echo "  - 仓库地址: $REPO_URL"
echo "  - Profile: $PROFILE"
echo "  - 令牌有效期: 12 小时"
echo ""
echo "现在可以使用以下命令安装依赖："
echo "  poetry install"
echo ""
echo "💡 提示: 令牌将在 12 小时后过期，到时请重新运行此脚本"
