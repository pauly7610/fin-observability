'use client';

import { useState } from 'react';
import { useModelConfig, useRetrainStatus, useLeaderboard, useTriggerRetrain } from '@/hooks/useModelManagement';

export function ModelManagement() {
  const { config, isLoading: configLoading, updateModel } = useModelConfig();
  const { status: retrainStatus, isLoading: retrainLoading } = useRetrainStatus();
  const { entries: leaderboard, isLoading: leaderboardLoading } = useLeaderboard();
  const triggerRetrain = useTriggerRetrain();

  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    const models = config?.available_models?.[provider];
    if (models && models.length > 0) {
      setSelectedModel(models[0].id);
    }
  };

  const handleApplyModel = () => {
    if (selectedProvider && selectedModel) {
      updateModel.mutate({ provider: selectedProvider, model: selectedModel });
    }
  };

  const currentProvider = config?.provider || 'none';
  const currentModel = config?.model || 'heuristic fallback';
  const isLLMActive = config?.source === 'llm';

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">LLM Configuration</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs text-gray-500 mb-1">Mode</div>
            <div className="flex items-center gap-2">
              <span className={`inline-block w-2 h-2 rounded-full ${isLLMActive ? 'bg-purple-500' : 'bg-gray-400'}`} />
              <span className="text-sm font-semibold">
                {isLLMActive ? 'LLM' : 'Heuristic'}
              </span>
            </div>
          </div>
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs text-gray-500 mb-1">Provider</div>
            <div className="text-sm font-semibold capitalize">{currentProvider}</div>
          </div>
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs text-gray-500 mb-1">Model</div>
            <div className="text-sm font-semibold">{currentModel}</div>
          </div>
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-xs text-gray-500 mb-1">Fallback Active</div>
            <div className="text-sm font-semibold">
              {config?.fallback_active ? 'Yes' : 'No'}
            </div>
          </div>
        </div>

        {/* Model Selector */}
        {config && !configLoading && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Provider</label>
                <select
                  value={selectedProvider || currentProvider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="block w-40 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {config.available_providers.map((p) => (
                    <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="block w-64 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {(config.available_models[selectedProvider || currentProvider] || []).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.tier}) — {m.finance_accuracy}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleApplyModel}
                disabled={updateModel.isPending}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {updateModel.isPending ? 'Applying...' : 'Apply'}
              </button>
            </div>
            {updateModel.isSuccess && (
              <p className="mt-2 text-xs text-green-600">Model updated successfully.</p>
            )}
            {updateModel.isError && (
              <p className="mt-2 text-xs text-red-600">Failed to update model.</p>
            )}
          </div>
        )}
      </div>

      {/* Retraining */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">ML Model Retraining</h3>
          <button
            onClick={() => triggerRetrain.mutate()}
            disabled={triggerRetrain.isPending}
            className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-md hover:bg-amber-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {triggerRetrain.isPending ? 'Retraining...' : 'Trigger Retrain'}
          </button>
        </div>
        {retrainStatus && !retrainLoading && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-xs text-gray-500 mb-1">Last Retrain</div>
              <div className="text-sm font-semibold">
                {retrainStatus.last_retrain
                  ? new Date(retrainStatus.last_retrain).toLocaleString()
                  : 'Never'}
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-xs text-gray-500 mb-1">Retrain Count</div>
              <div className="text-sm font-semibold">{retrainStatus.retrain_count}</div>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div className="text-xs text-gray-500 mb-1">Schedule</div>
              <div className="text-sm font-semibold">Every {retrainStatus.schedule_hours}h</div>
            </div>
          </div>
        )}
        {triggerRetrain.isSuccess && (
          <p className="mt-3 text-xs text-green-600">Retraining completed successfully.</p>
        )}
        {triggerRetrain.isError && (
          <p className="mt-3 text-xs text-red-600">Retraining failed.</p>
        )}
      </div>

      {/* Leaderboard */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Leaderboard</h3>
        {leaderboardLoading ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : leaderboard.length === 0 ? (
          <p className="text-sm text-gray-500">No model versions evaluated yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Version</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">F1</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">Precision</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">Recall</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">Predictions</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">Date</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, idx) => (
                  <tr key={entry.model_version} className={`border-b border-gray-100 ${idx === 0 ? 'bg-green-50' : ''}`}>
                    <td className="py-2 px-3 font-medium">
                      {idx === 0 && <span className="mr-1">&#9733;</span>}
                      {entry.model_version}
                    </td>
                    <td className="py-2 px-3 text-right font-semibold">{(entry.f1_score * 100).toFixed(1)}%</td>
                    <td className="py-2 px-3 text-right">{(entry.precision * 100).toFixed(1)}%</td>
                    <td className="py-2 px-3 text-right">{(entry.recall * 100).toFixed(1)}%</td>
                    <td className="py-2 px-3 text-right">{entry.total_predictions}</td>
                    <td className="py-2 px-3 text-right text-gray-500">
                      {new Date(entry.timestamp).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
