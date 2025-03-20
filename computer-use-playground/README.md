# Computer Use Playground

<img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-blue.svg?logo=TypeScript&logoColor=white" />

Watch computer use models control a cloud desktop through a web interface powered by Scrapybara Act SDK.

## Features

- Interactive chat and instance management interface
- Support for OpenAI CUA and Anthropic Claude models
- Ubuntu and browser instance options
- Real-time streaming of responses and instance desktop
- Tool use visualization

## Prerequisites

- Node.js 18+
- npm or pnpm
- Scrapybara API key (get one at [scrapybara.com](https://scrapybara.com))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/scrapybara/scrapybara-cookbook.git
cd scrapybara-cookbook/chat-playground
```

2. Install dependencies:

```bash
npm install
# or
pnpm install
```

3. Start the development server:

```bash
npm run dev
# or
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## How It Works

The Chat Playground demonstrates how to build an AI assistant with the Scrapybara Act SDK:

1. **Frontend (`page.tsx`)**:

   - Manages the chat interface and user interactions
   - Displays a live interactive instance stream
   - Visualizes tool calls and results

2. **Server Actions (`server/actions.ts`)**:

   - Contains Next.js server actions for instance management
   - `startInstance`: Initializes a new Ubuntu or browser instance
   - `stopInstance`: Safely terminates running instances

3. **Backend API (`api/chat/route.ts`)**:
   - Creates a streaming response using ReadableStream
   - Configures the AI model (OpenAI or Claude) with appropriate tools
   - Calls `act` and streams each step of the AI's response back to the frontend

You can customize the models and tools by modifying the configuration in these files.

## Project Structure

```
.
├── src/
    ├── app/
    |   ├── page.tsx  # Main chat interface
    |   └── api/chat/ # API endpoint for chat
    ├── server/
    |   └── actions.ts # Server actions for instance management
    └── components/   # UI components
```

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new) from the creators of Next.js.

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
