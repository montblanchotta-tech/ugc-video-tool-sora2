#!/bin/bash

# Sora 2 API統合動画生成SaaS - Vercelデプロイスクリプト

echo "🚀 Sora 2 API統合動画生成SaaS - Vercelデプロイメント"
echo "=================================================="

# 1. GitHubリポジトリの確認
echo "📋 1. GitHubリポジトリの確認"
if git remote -v | grep -q "origin"; then
    echo "✅ リモートリポジトリが設定されています"
    git remote -v
else
    echo "❌ リモートリポジトリが設定されていません"
    echo "以下のコマンドを実行してください:"
    echo "git remote add origin https://github.com/yourusername/ugc-video-tool-sora2.git"
    exit 1
fi

# 2. 最新の変更をコミット
echo ""
echo "📝 2. 最新の変更をコミット"
git add .
git commit -m "Update: Vercel deployment configuration"

# 3. GitHubにプッシュ
echo ""
echo "⬆️  3. GitHubにプッシュ"
git push origin main

# 4. Vercel CLIの確認
echo ""
echo "🔧 4. Vercel CLIの確認"
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLIがインストールされています"
    vercel --version
else
    echo "❌ Vercel CLIがインストールされていません"
    echo "以下のコマンドを実行してください:"
    echo "npm install -g vercel"
    exit 1
fi

# 5. 環境変数の確認
echo ""
echo "🔑 5. 環境変数の確認"
echo "以下の環境変数がVercelダッシュボードで設定されていることを確認してください:"
echo "- OPENAI_API_KEY"
echo "- GEMINI_API_KEY"
echo "- FISHAUDIO_API_KEY"
echo "- HEDRA_API_KEY"
echo "- WEBHOOK_SECRET"

# 6. デプロイ実行
echo ""
echo "🚀 6. Vercelにデプロイ"
read -p "デプロイを実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    vercel --prod
else
    echo "デプロイをキャンセルしました"
fi

echo ""
echo "✅ デプロイメント完了！"
echo "Vercelダッシュボードでデプロイ状況を確認してください:"
echo "https://vercel.com/dashboard"
