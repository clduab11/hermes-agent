/**
 * Leads Management Page
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../services/api';

export default function LeadsPage() {
  const [filter, setFilter] = useState({ status: '', source: '' });
  const queryClient = useQueryClient();

  const { data: leads, isLoading } = useQuery({
    queryKey: ['leads', filter],
    queryFn: async () => {
      const response = await leadsApi.getAll(filter);
      return response.data;
    },
  });

  const statusOptions = [
    'new', 'contacted', 'qualified', 'demo_scheduled', 
    'proposal_sent', 'negotiating', 'won', 'lost'
  ];

  const getStatusBadge = (status) => {
    const colors = {
      new: 'badge-primary',
      contacted: 'badge-info',
      qualified: 'badge-accent',
      demo_scheduled: 'badge-secondary',
      proposal_sent: 'badge-warning',
      negotiating: 'badge-warning',
      won: 'badge-success',
      lost: 'badge-error',
    };
    return colors[status] || 'badge-neutral';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Lead Pipeline</h1>
        <button className="btn btn-primary">+ Add New Lead</button>
      </div>

      {/* Filters */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="form-control">
              <label className="label">
                <span className="label-text">Status</span>
              </label>
              <select
                className="select select-bordered"
                value={filter.status}
                onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              >
                <option value="">All Statuses</option>
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Source</span>
              </label>
              <select
                className="select select-bordered"
                value={filter.source}
                onChange={(e) => setFilter({ ...filter, source: e.target.value })}
              >
                <option value="">All Sources</option>
                <option value="website">Website</option>
                <option value="referral">Referral</option>
                <option value="social">Social Media</option>
                <option value="campaign">Campaign</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      ) : (
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <div className="overflow-x-auto">
              <table className="table table-zebra">
                <thead>
                  <tr>
                    <th>Firm Name</th>
                    <th>Contact</th>
                    <th>Status</th>
                    <th>Pipeline Value</th>
                    <th>Probability</th>
                    <th>Source</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {leads?.map((lead) => (
                    <tr key={lead.id}>
                      <td>
                        <div className="font-bold">{lead.firm_name}</div>
                        <div className="text-sm opacity-50">{lead.firm_size}</div>
                      </td>
                      <td>
                        <div>{lead.contact_name}</div>
                        <div className="text-sm opacity-50">{lead.contact_email}</div>
                      </td>
                      <td>
                        <span className={`badge ${getStatusBadge(lead.status)}`}>
                          {lead.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>${lead.pipeline_value?.toLocaleString() || '0'}/mo</td>
                      <td>{lead.probability || 0}%</td>
                      <td>{lead.source || 'N/A'}</td>
                      <td>{new Date(lead.created_at).toLocaleDateString()}</td>
                      <td>
                        <button className="btn btn-ghost btn-xs">Edit</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
