/*
 * Icon — one wrapper around Hugeicons so pages can say <Icon name="Target02Icon" />.
 *
 * Only the icons listed in ICONS are bundled (importing the whole set would
 * add megabytes). To use a new one: find it at https://hugeicons.com (free
 * set), add it to the import and the ICONS map below.
 *
 * Icons are decorative by default (aria-hidden); pass `label` when an icon
 * is the only content of a control.
 */
import { HugeiconsIcon } from '@hugeicons/react';
import {
  Add01Icon, Alert02Icon, Analytics01Icon, ArrowDown01Icon, ArrowLeft01Icon, ArrowRight01Icon,
  ArrowRight02Icon, ArrowTurnBackwardIcon, ArrowUpRight01Icon, Book02Icon, BulbIcon, Calendar03Icon,
  Cancel01Icon, ChartLineData02Icon, CheckmarkCircle02Icon, Clock01Icon, Copy01Icon, DashboardSquare01Icon,
  Delete02Icon, Download01Icon, HelpCircleIcon, InformationCircleIcon, Login01Icon, Logout01Icon,
  Menu01Icon, Notebook01Icon, PencilEdit01Icon, PieChartIcon, Plug01Icon, RefreshIcon, Search01Icon,
  Settings02Icon, Shield01Icon, SparklesIcon, Store01Icon, Target02Icon, Tick02Icon, UserCircleIcon,
} from '@hugeicons/core-free-icons';

const ICONS = {
  Add01Icon, Alert02Icon, Analytics01Icon, ArrowDown01Icon, ArrowLeft01Icon, ArrowRight01Icon,
  ArrowRight02Icon, ArrowTurnBackwardIcon, ArrowUpRight01Icon, Book02Icon, BulbIcon, Calendar03Icon,
  Cancel01Icon, ChartLineData02Icon, CheckmarkCircle02Icon, Clock01Icon, Copy01Icon, DashboardSquare01Icon,
  Delete02Icon, Download01Icon, HelpCircleIcon, InformationCircleIcon, Login01Icon, Logout01Icon,
  Menu01Icon, Notebook01Icon, PencilEdit01Icon, PieChartIcon, Plug01Icon, RefreshIcon, Search01Icon,
  Settings02Icon, Shield01Icon, SparklesIcon, Store01Icon, Target02Icon, Tick02Icon, UserCircleIcon,
};

export default function Icon({ name, size = 18, strokeWidth = 1.8, label, className = '', style }) {
  const icon = ICONS[name];
  if (!icon) return null;
  return (
    <span
      className={`icon ${className}`}
      style={{ display: 'inline-flex', flex: 'none', ...style }}
      aria-hidden={label ? undefined : true}
      role={label ? 'img' : undefined}
      aria-label={label}
    >
      <HugeiconsIcon icon={icon} size={size} strokeWidth={strokeWidth} />
    </span>
  );
}
