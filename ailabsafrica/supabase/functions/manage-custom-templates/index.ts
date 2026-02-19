import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response(null, { headers: corsHeaders });
	}

	try {
		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseServiceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
		const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;

		const supabaseAuth = createClient(supabaseUrl, supabaseAnonKey, {
			global: { headers: { Authorization: req.headers.get("Authorization") || "" } },
		});

		const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

		// Get authenticated user
		const { data: { user }, error: authError } = await supabaseAuth.auth.getUser();
		if (authError || !user) {
			return new Response(JSON.stringify({ error: "Unauthorized" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		const { action, ...data } = await req.json();

		switch (action) {
			case "create":
				return await createTemplate(supabase, user.id, data);

			case "update":
				return await updateTemplate(supabase, user.id, data);

			case "delete":
				return await deleteTemplate(supabase, user.id, data);

			case "list":
				return await listTemplates(supabase, user.id, data);

			case "get":
				return await getTemplate(supabase, user.id, data);

			case "duplicate":
				return await duplicateTemplate(supabase, user.id, data);

			case "toggle_favorite":
				return await toggleFavorite(supabase, user.id, data);

			case "increment_usage":
				return await incrementUsage(supabase, data);

			case "search":
				return await searchTemplates(supabase, user.id, data);

			default:
				return new Response(JSON.stringify({ error: "Invalid action" }), {
					status: 400,
					headers: { ...corsHeaders, "Content-Type": "application/json" },
				});
		}
	} catch (error: any) {
		console.error("manage-custom-templates error:", error);
		return new Response(JSON.stringify({ error: error?.message || "Internal error" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});

async function createTemplate(supabase: any, userId: string, data: any) {
	const {
		name,
		description,
		category,
		difficulty,
		system_prompt,
		sample_questions = [],
		use_cases = [],
		tags = [],
		features = [],
		is_public = false,
		parent_template_id = null
	} = data;

	if (!name || !category || !difficulty || !system_prompt) {
		return new Response(JSON.stringify({ error: "Missing required fields" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	const { data: template, error } = await supabase
		.from("custom_templates")
		.insert({
			user_id: userId,
			name,
			description,
			category,
			difficulty,
			system_prompt,
			sample_questions,
			use_cases,
			tags,
			features,
			is_public,
			parent_template_id
		})
		.select()
		.single();

	if (error) {
		console.error("Create template error:", error);
		return new Response(JSON.stringify({ error: "Failed to create template" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ template }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function updateTemplate(supabase: any, userId: string, data: any) {
	const { id, ...updateData } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	// Verify ownership
	const { data: existing, error: checkError } = await supabase
		.from("custom_templates")
		.select("id")
		.eq("id", id)
		.eq("user_id", userId)
		.single();

	if (checkError || !existing) {
		return new Response(JSON.stringify({ error: "Template not found or access denied" }), {
			status: 404,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	const { data: template, error } = await supabase
		.from("custom_templates")
		.update({
			...updateData,
			version: updateData.version ? updateData.version + 1 : undefined
		})
		.eq("id", id)
		.eq("user_id", userId)
		.select()
		.single();

	if (error) {
		console.error("Update template error:", error);
		return new Response(JSON.stringify({ error: "Failed to update template" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ template }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function deleteTemplate(supabase: any, userId: string, data: any) {
	const { id } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	const { error } = await supabase
		.from("custom_templates")
		.delete()
		.eq("id", id)
		.eq("user_id", userId);

	if (error) {
		console.error("Delete template error:", error);
		return new Response(JSON.stringify({ error: "Failed to delete template" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ success: true }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function listTemplates(supabase: any, userId: string, data: any) {
	const {
		category = null,
		difficulty = null,
		is_favorite = null,
		is_public = null,
		limit = 50,
		offset = 0,
		sort_by = "created_at",
		sort_order = "desc"
	} = data;

	let query = supabase
		.from("custom_templates")
		.select("*")
		.or(`user_id.eq.${userId},is_public.eq.true`);

	if (category) query = query.eq("category", category);
	if (difficulty) query = query.eq("difficulty", difficulty);
	if (is_favorite !== null) query = query.eq("is_favorite", is_favorite);
	if (is_public !== null) query = query.eq("is_public", is_public);

	query = query
		.order(sort_by, { ascending: sort_order === "asc" })
		.range(offset, offset + limit - 1);

	const { data: templates, error, count } = await query;

	if (error) {
		console.error("List templates error:", error);
		return new Response(JSON.stringify({ error: "Failed to list templates" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ templates, count }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function getTemplate(supabase: any, userId: string, data: any) {
	const { id } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	const { data: template, error } = await supabase
		.from("custom_templates")
		.select("*")
		.eq("id", id)
		.or(`user_id.eq.${userId},is_public.eq.true`)
		.single();

	if (error || !template) {
		return new Response(JSON.stringify({ error: "Template not found" }), {
			status: 404,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ template }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function duplicateTemplate(supabase: any, userId: string, data: any) {
	const { id, new_name } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	// Get original template
	const { data: original, error: getError } = await supabase
		.from("custom_templates")
		.select("*")
		.eq("id", id)
		.or(`user_id.eq.${userId},is_public.eq.true`)
		.single();

	if (getError || !original) {
		return new Response(JSON.stringify({ error: "Template not found" }), {
			status: 404,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	// Create duplicate
	const { data: duplicate, error: createError } = await supabase
		.from("custom_templates")
		.insert({
			user_id: userId,
			name: new_name || `${original.name} (Copy)`,
			description: original.description,
			category: original.category,
			difficulty: original.difficulty,
			system_prompt: original.system_prompt,
			sample_questions: original.sample_questions,
			use_cases: original.use_cases,
			tags: original.tags,
			features: original.features,
			is_public: false,
			parent_template_id: original.id,
			version: 1
		})
		.select()
		.single();

	if (createError) {
		console.error("Duplicate template error:", createError);
		return new Response(JSON.stringify({ error: "Failed to duplicate template" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ template: duplicate }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function toggleFavorite(supabase: any, userId: string, data: any) {
	const { id } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	// Get current favorite status
	const { data: template, error: getError } = await supabase
		.from("custom_templates")
		.select("is_favorite")
		.eq("id", id)
		.eq("user_id", userId)
		.single();

	if (getError || !template) {
		return new Response(JSON.stringify({ error: "Template not found" }), {
			status: 404,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	// Toggle favorite status
	const { data: updated, error: updateError } = await supabase
		.from("custom_templates")
		.update({ is_favorite: !template.is_favorite })
		.eq("id", id)
		.eq("user_id", userId)
		.select()
		.single();

	if (updateError) {
		console.error("Toggle favorite error:", updateError);
		return new Response(JSON.stringify({ error: "Failed to toggle favorite" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ template: updated }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function incrementUsage(supabase: any, data: any) {
	const { id } = data;

	if (!id) {
		return new Response(JSON.stringify({ error: "Template ID required" }), {
			status: 400,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	const { error } = await supabase.rpc("increment_template_usage", { template_id: id });

	if (error) {
		console.error("Increment usage error:", error);
		return new Response(JSON.stringify({ error: "Failed to increment usage" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ success: true }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

async function searchTemplates(supabase: any, userId: string, data: any) {
	const {
		query = "",
		category = null,
		difficulty = null,
		tags = [],
		limit = 50,
		offset = 0
	} = data;

	let searchQuery = supabase
		.from("custom_templates")
		.select("*")
		.or(`user_id.eq.${userId},is_public.eq.true`);

	if (query) {
		searchQuery = searchQuery.or(`name.ilike.%${query}%,description.ilike.%${query}%`);
	}

	if (category) searchQuery = searchQuery.eq("category", category);
	if (difficulty) searchQuery = searchQuery.eq("difficulty", difficulty);
	if (tags.length > 0) {
		searchQuery = searchQuery.overlaps("tags", tags);
	}

	const { data: templates, error } = await searchQuery
		.order("usage_count", { ascending: false })
		.range(offset, offset + limit - 1);

	if (error) {
		console.error("Search templates error:", error);
		return new Response(JSON.stringify({ error: "Failed to search templates" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}

	return new Response(JSON.stringify({ templates }), {
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}

