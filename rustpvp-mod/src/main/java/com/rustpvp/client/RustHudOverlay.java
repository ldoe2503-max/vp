package com.rustpvp.client;

import com.rustpvp.item.ModItems;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraftforge.client.gui.overlay.ForgeGui;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;

/**
 * Собственный HUD в духе Rust: тёмная плашка снизу слева с полоской здоровья
 * и счётчиком патронов, если в руке автомат. Рисуется закрашенными
 * прямоугольниками через GuiGraphics -- никаких текстур/ассетов из игры Rust.
 */
public class RustHudOverlay implements IGuiOverlay {

    private static final int PANEL_X = 8;
    private static final int BAR_WIDTH = 120;
    private static final int BAR_HEIGHT = 10;

    private static final int COLOR_PANEL_BG = 0xC0161613;
    private static final int COLOR_BAR_BG = 0xFF2A2A26;
    private static final int COLOR_HEALTH = 0xFFB2312D;
    private static final int COLOR_HEALTH_LOW = 0xFFE8461D;
    private static final int COLOR_AMMO = 0xFFC7A23A;
    private static final int COLOR_TEXT = 0xFFE8E4D8;

    @Override
    public void render(ForgeGui gui, GuiGraphics graphics, float partialTick, int screenWidth, int screenHeight) {
        LocalPlayer player = gui.getMinecraft().player;
        if (player == null || gui.getMinecraft().options.hideGui) {
            return;
        }

        int panelY = screenHeight - 58;
        int panelHeight = 46;

        graphics.fill(PANEL_X, panelY, PANEL_X + BAR_WIDTH + 16, panelY + panelHeight, COLOR_PANEL_BG);

        // --- Полоса здоровья ---
        float health = player.getHealth();
        float maxHealth = player.getMaxHealth();
        float healthRatio = maxHealth <= 0 ? 0 : Math.max(0, Math.min(1, health / maxHealth));
        int barX = PANEL_X + 8;
        int healthY = panelY + 8;

        graphics.fill(barX, healthY, barX + BAR_WIDTH, healthY + BAR_HEIGHT, COLOR_BAR_BG);
        int healthFillWidth = (int) (BAR_WIDTH * healthRatio);
        int healthColor = healthRatio <= 0.3F ? COLOR_HEALTH_LOW : COLOR_HEALTH;
        if (healthFillWidth > 0) {
            graphics.fill(barX, healthY, barX + healthFillWidth, healthY + BAR_HEIGHT, healthColor);
        }
        graphics.drawString(gui.getMinecraft().font,
                String.format("%.0f / %.0f", health, maxHealth),
                barX + 4, healthY + 1, COLOR_TEXT, true);

        // --- Патроны (только если в руке автомат) ---
        int ammoY = healthY + BAR_HEIGHT + 6;
        boolean holdingAk = player.getMainHandItem().is(ModItems.AK47.get())
                || player.getOffhandItem().is(ModItems.AK47.get());

        if (holdingAk) {
            int ammoCount = 0;
            for (var stack : player.getInventory().items) {
                if (stack.is(ModItems.AK_AMMO.get())) {
                    ammoCount += stack.getCount();
                }
            }
            graphics.fill(barX, ammoY, barX + BAR_WIDTH, ammoY + BAR_HEIGHT, COLOR_BAR_BG);
            graphics.drawString(gui.getMinecraft().font,
                    "AK-47 · " + ammoCount + " патронов",
                    barX + 4, ammoY + 1, COLOR_AMMO, true);
        }
    }
}
