'use client';
import React from 'react';
import { Header } from "@/components/ui/header-2";

export default function HeaderDemo() {
	return (
		<div className="w-full">
			<Header />

			<main className="mx-auto min-h-screen w-full max-w-3xl px-4 py-12">
				<div className="space-y-2 mb-4">
					<div className="bg-zinc-100 h-6 w-4/6 rounded-md border border-black/10" />
					<div className="bg-zinc-100 h-6 w-1/2 rounded-md border border-black/10" />
				</div>
				<div className="flex gap-2 mb-8">
					<div className="bg-zinc-100 h-3 w-14 rounded-md border border-black/10" />
					<div className="bg-zinc-100 h-3 w-12 rounded-md border border-black/10" />
				</div>

				{Array.from({ length: 7 }).map((_, i) => (
					<div key={i} className="space-y-2 mb-8">
						<div className="bg-zinc-100 h-4 w-full rounded-md border border-black/10" />
						<div className="bg-zinc-100 h-4 w-full rounded-md border border-black/10" />
						<div className="bg-zinc-100 h-4 w-full rounded-md border border-black/10" />
						<div className="bg-zinc-100 h-4 w-1/2 rounded-md border border-black/10" />
					</div>
				))}
			</main>
		</div>
	);
}
