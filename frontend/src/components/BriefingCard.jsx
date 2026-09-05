import React from 'react';
import { motion } from 'framer-motion';

export default function BriefingCard({ title, data, count, type }) {
  const getBadgeClass = (status) => {
    switch (status) {
      case 'out_of_stock':
      case 'spike':
        return 'bg-danger text-white';
      case 'below_reorder':
      case 'drop':
        return 'bg-warning text-white';
      case 'velocity_risk':
        return 'bg-caution text-white';
      default:
        return 'bg-muted text-white';
    }
  };

  const getLabel = (status) => {
    switch (status) {
      case 'out_of_stock': return 'Out of Stock';
      case 'below_reorder': return 'Below Reorder';
      case 'velocity_risk': return 'Velocity Risk';
      case 'spike': return 'Spike';
      case 'drop': return 'Drop';
      default: return status;
    }
  };

  const renderItem = (item, index) => {
    let badgeText = '';
    let badgeClass = 'bg-muted text-white';
    let subtitle = '';

    if (type === 'stockout') {
      badgeText = getLabel(item.status);
      badgeClass = getBadgeClass(item.status);
      subtitle = `${item.current_stock} in stock · reorder at ${item.reorder_level} · avg ${item.avg_daily_velocity}/day`;
    } else if (type === 'deadstock') {
      badgeText = item.category || 'Dead Stock';
      subtitle = `$${Number(item.dead_stock_value).toFixed(2)} tied up · ${item.current_stock} units`;
    } else if (type === 'anomaly') {
      badgeText = getLabel(item.type);
      badgeClass = getBadgeClass(item.type);
      const sign = item.change_pct > 0 ? '+' : '';
      subtitle = `${item.actual_units} units vs usual ${item.usual_daily_units} (${sign}${item.change_pct}%)`;
    }

    return (
      <li key={index} className="flex flex-col gap-2 py-4 border-b border-dashed border-border text-sm group">
        <div className="flex items-start justify-between">
          <span className="font-display font-semibold text-text uppercase tracking-wide">
            {item.name}
          </span>
          <span className={`shrink-0 rounded-none text-[10px] font-bold uppercase tracking-widest px-2 py-1 ${badgeClass}`}>
            {badgeText}
          </span>
        </div>
        <div className="flex items-center justify-between mt-1">
           <span className="text-text text-xs uppercase tracking-wider opacity-80">{subtitle}</span>
           <em className="text-primary not-italic font-medium text-xs ml-1">{item.store_id || item.date}</em>
        </div>
      </li>
    );
  };

  return (
    <motion.article
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-transparent border-r border-b border-dashed border-border p-6 md:p-8 flex flex-col min-h-[350px] max-h-[500px]"
    >
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-text">
        <h3 className="m-0 text-lg font-display font-bold text-text uppercase tracking-widest">{title}</h3>
        <span className="text-primary font-bold text-sm">
          [{count}]
        </span>
      </div>
      <ul className="list-none m-0 p-0 overflow-y-auto flex-1 pr-2">
        {data.length === 0 ? (
          <li className="text-text opacity-70 uppercase tracking-widest text-xs py-6">No items found.</li>
        ) : (
          data.map((item, i) => renderItem(item, i))
        )}
      </ul>
    </motion.article>
  );
}
