import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

function parseModelSpec(args: string, currentProvider?: string): { provider: string; modelId: string; usage?: string } {
	const trimmed = args.trim();
	if (!trimmed) {
		throw new Error("Usage: /model:set <provider> <modelId> | <provider>/<modelId> | <modelId> (uses current provider)");
	}

	const spaceIndex = trimmed.search(/\s/);
	if (spaceIndex !== -1) {
		const provider = trimmed.slice(0, spaceIndex).trim();
		const modelId = trimmed.slice(spaceIndex + 1).trim();
		if (!provider || !modelId) {
			throw new Error("Usage: /model:set <provider> <modelId> | <provider>/<modelId> | <modelId> (uses current provider)");
		}
		return { provider, modelId, usage: `${provider} ${modelId}` };
	}

	const slashIndex = trimmed.indexOf("/");
	if (slashIndex !== -1) {
		const provider = trimmed.slice(0, slashIndex).trim();
		const modelId = trimmed.slice(slashIndex + 1).trim();
		if (!provider || !modelId) {
			throw new Error("Usage: /model:set <provider> <modelId> | <provider>/<modelId> | <modelId> (uses current provider)");
		}
		return { provider, modelId, usage: `${provider}/${modelId}` };
	}

	if (!currentProvider) {
		throw new Error("Usage: /model:set <provider> <modelId> | <provider>/<modelId> | <modelId> (uses current provider)");
	}

	return { provider: currentProvider, modelId: trimmed, usage: `${currentProvider}/${trimmed}` };
}

export default function modelSwitchExtension(pi: ExtensionAPI) {
	pi.registerCommand("model:set", {
		description: "Switch the active model for this session",
		handler: async (args, ctx) => {
			try {
				await ctx.waitForIdle();

				const currentProvider = ctx.model?.provider;
				const { provider, modelId } = parseModelSpec(args, currentProvider);
				const model = ctx.modelRegistry.find(provider, modelId);
				if (!model) {
					ctx.ui.notify(`Unknown model: ${provider}/${modelId}`, "error");
					return;
				}

				const changed = await pi.setModel(model);
				if (!changed) {
					ctx.ui.notify(`Model found, but authentication is not configured for ${provider}/${modelId}.`, "error");
					return;
				}

				ctx.ui.notify(`Switched to ${provider}/${modelId}`, "info");
			} catch (error) {
				ctx.ui.notify(error instanceof Error ? error.message : String(error), "error");
			}
		},
	});
}
